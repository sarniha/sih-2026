"""
anpr_pipeline.py — ANPR + Incident Detection Main Entrypoint

Pipeline stages (per processed frame):
  1. Vehicle detection + tracking  (YOLOv8n COCO + ByteTrack)
  2. Incident detection            (Method A: speed anomaly)
  3. Plate detection               (pretrained YOLO LP detector / classical CV)
  4. OCR                           (EasyOCR with preprocessing)
  5. Alert packaging               (maps to backend EventCreate schema)
  6. Secure push                   (X-Service-Token, retry queue)

Usage:
    python anpr_pipeline.py [--video path/to/file.mp4] [--dry-run] [--no-display]

Environment:
    SERVICE_TOKEN  — set via: $env:SERVICE_TOKEN = "..."
                     (same token as backend .env SERVICE_TOKEN)

The backend auto-spawns an Incident row from every "hit_run" event, attaches
evidence, and broadcasts over WebSocket — no additional work needed here.
"""

import argparse
import math
import time
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
from ultralytics import YOLO

from alert_builder import build_alert, strip_meta
from alert_pusher import AlertPusher
from config import (
    BACKEND_URL,
    CONFIDENCE_THRESHOLD,
    DEFAULT_GPS,
    EVIDENCE_DIR,
    INPUT_SIZE,
    MODEL_PATH,
    PLATE_DIR,
    PROCESS_EVERY_N_FRAMES,
    SEND_TO_BACKEND,
    TRACKER_CONFIG,
    VEHICLE_CLASSES,
    VIDEO_PATH,
)
from evidence_saver import EvidenceSaver
from incident_detector import IncidentDetector
from ocr_reader import OCRReader
from plate_detector import PlateDetector

# COCO class names for vehicle classes
_COCO_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}

# Colour palette for on-screen overlay (BGR)
_COLOUR_NORMAL   = (0,  200,  0)    # green
_COLOUR_INCIDENT = (0,   0, 255)    # red
_COLOUR_PLATE    = (0, 255, 255)    # yellow


# ──────────────────────────────────────────────────────────────────────────────
# Vehicle detector (thin wrapper matching vehicle-tracking/detector.py pattern)
# ──────────────────────────────────────────────────────────────────────────────

class VehicleDetector:
    def __init__(self):
        print(f"[VehicleDetector] Loading {MODEL_PATH} …")
        self.model = YOLO(MODEL_PATH)
        print("[VehicleDetector] ✅ YOLOv8n loaded")

    def track(self, frame: np.ndarray) -> Tuple[List[dict], object]:
        results = self.model.track(
            frame,
            classes=VEHICLE_CLASSES,
            persist=True,
            tracker=TRACKER_CONFIG,
            conf=CONFIDENCE_THRESHOLD,
            imgsz=INPUT_SIZE,
            verbose=False,
        )
        detections = []
        boxes = results[0].boxes
        if boxes is not None and boxes.id is not None:
            for box, track_id, conf, cls_id in zip(
                boxes.xyxy, boxes.id, boxes.conf, boxes.cls
            ):
                x1, y1, x2, y2 = (int(v) for v in box)
                detections.append({
                    "track_id":   int(track_id),
                    "center_x":   (x1 + x2) // 2,
                    "center_y":   (y1 + y2) // 2,
                    "bbox":       (x1, y1, x2, y2),
                    "confidence": float(conf),
                    "class_name": _COCO_NAMES.get(int(cls_id), "vehicle"),
                })
        return detections, results[0]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _find_det(track_id: int, detections: List[dict]) -> Optional[dict]:
    for d in detections:
        if d["track_id"] == track_id:
            return d
    return None


def _crop(frame: np.ndarray, bbox: Tuple[int, int, int, int],
          pad: int = 10) -> np.ndarray:
    """Crop frame to bbox with optional padding, clamped to frame bounds."""
    h, w = frame.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)
    return frame[y1:y2, x1:x2]


def _plate_bbox_to_fullframe(
    vehicle_bbox: Tuple[int, int, int, int],
    plate_bbox_in_crop: Tuple[int, int, int, int],
    pad: int = 10,
) -> Tuple[int, int, int, int]:
    """Convert plate bbox (relative to vehicle crop) → full-frame coords."""
    vx1, vy1, _, _ = vehicle_bbox
    offset_x = max(0, vx1 - pad)
    offset_y = max(0, vy1 - pad)
    px1, py1, px2, py2 = plate_bbox_in_crop
    return (px1 + offset_x, py1 + offset_y, px2 + offset_x, py2 + offset_y)


def _draw_overlay(
    frame:       np.ndarray,
    detections:  List[dict],
    flagged_ids: set,
    fps:         float,
    plate_mode:  str,
) -> None:
    """Draw all vehicle boxes, highlight incidents, show HUD."""
    for det in detections:
        tid   = det["track_id"]
        x1, y1, x2, y2 = det["bbox"]
        colour = _COLOUR_INCIDENT if tid in flagged_ids else _COLOUR_NORMAL
        cv2.rectangle(frame, (x1, y1), (x2, y2), colour, 2)
        label = f"#{tid} {det['class_name']}"
        cv2.putText(frame, label, (x1, y1 - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)

    # HUD
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
    cv2.putText(frame, f"Plate mode: {plate_mode}", (10, 58),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    cv2.putText(frame, f"Vehicles: {len(detections)}", (10, 82),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)


# ──────────────────────────────────────────────────────────────────────────────
# Main pipeline
# ──────────────────────────────────────────────────────────────────────────────

def main(video_path: str, dry_run: bool, no_display: bool):
    if dry_run:
        import config as cfg
        cfg.SEND_TO_BACKEND = False
        print("[Pipeline] 🔶 DRY RUN — alerts logged locally, not sent to backend")

    # Initialise components
    vehicle_detector  = VehicleDetector()
    incident_detector = IncidentDetector()
    plate_detector    = PlateDetector()
    ocr_reader        = OCRReader()
    evidence_saver    = EvidenceSaver(EVIDENCE_DIR, PLATE_DIR)
    alert_pusher      = AlertPusher(BACKEND_URL)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError(f"[Pipeline] Cannot open video source: {video_path}")

    video_fps   = cap.get(cv2.CAP_PROP_FPS) or 25.0
    frame_count = 0
    prev_time   = time.time()
    display_fps = 0.0

    last_detections: List[dict] = []
    flagged_ids: set = set()

    print(f"[Pipeline] ▶ Processing: {video_path} @ {video_fps:.1f} fps")
    print(f"[Pipeline] Plate detector mode: {plate_detector.mode}")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[Pipeline] End of video / stream lost.")
            break

        frame_count += 1
        now = time.time()
        display_fps = 1.0 / max(now - prev_time, 1e-6)
        prev_time   = now

        # ── Step 1 + 2: Detect vehicles + check for incidents ─────────────────
        if frame_count % PROCESS_EVERY_N_FRAMES == 0:
            last_detections, _ = vehicle_detector.track(frame)
            flagged_list        = incident_detector.update(last_detections)
            flagged_ids         = {f["track_id"] for f in flagged_list}

            # ── Steps 3-6: Full ANPR pipeline for each flagged vehicle ─────────
            for flag in flagged_list:
                tid = flag["track_id"]
                det = _find_det(tid, last_detections)
                if det is None:
                    continue

                vehicle_bbox = det["bbox"]
                vehicle_crop = _crop(frame, vehicle_bbox)

                print(f"\n[INCIDENT] track={tid} | {flag['incident_type']} | "
                      f"speed={flag['smoothed_speed_px_sec']} px/s")

                # ── Step 3: Plate detection ────────────────────────────────────
                plates = plate_detector.detect(vehicle_crop)
                plate_img           = None
                plate_bbox_fullframe = None

                if plates:
                    best_plate = plates[0]   # highest confidence
                    px1, py1, px2, py2, p_conf = best_plate
                    plate_img           = vehicle_crop[py1:py2, px1:px2]
                    plate_bbox_fullframe = _plate_bbox_to_fullframe(vehicle_bbox,
                                                                    (px1, py1, px2, py2))
                    print(f"[PLATE]    Detected ({plate_detector.mode}) "
                          f"conf={p_conf:.2f} bbox=({px1},{py1},{px2},{py2})")
                else:
                    print(f"[PLATE]    No plate region found ({plate_detector.mode})")

                # ── Step 4: OCR ───────────────────────────────────────────────
                raw_text, ocr_conf = (None, 0.0)
                clean_text         = None

                if plate_img is not None and plate_img.size > 0:
                    raw_text, ocr_conf = ocr_reader.read_plate(plate_img)
                    clean_text         = ocr_reader.clean_plate(raw_text)
                    print(f"[OCR]      raw='{raw_text}' → clean='{clean_text}' "
                          f"conf={ocr_conf:.3f}")
                else:
                    print("[OCR]      Skipped — no plate crop available")

                # ── Step 5: Save evidence frame ───────────────────────────────
                evidence_url = evidence_saver.save(
                    frame         = frame,
                    track_id      = tid,
                    incident_type = flag["incident_type"],
                    plate_text    = clean_text,
                    vehicle_bbox  = vehicle_bbox,
                    plate_bbox    = plate_bbox_fullframe,
                    plate_img     = plate_img,
                )
                print(f"[EVIDENCE] Saved → {evidence_url}")

                # ── Step 6: Build alert + push ────────────────────────────────
                alert = build_alert(
                    track_id       = tid,
                    incident_type  = flag["incident_type"],
                    plate_text     = clean_text,
                    plate_conf     = ocr_conf,
                    raw_plate_text = raw_text,
                    vehicle_bbox   = vehicle_bbox,
                    vehicle_class  = det["class_name"],
                    evidence_url   = evidence_url,
                    gps            = DEFAULT_GPS,
                    frame_num      = frame_count,
                    fps            = video_fps,
                    speed_px_sec   = flag["speed_px_sec"],
                )

                backend_payload = strip_meta(alert)
                alert_pusher.push(backend_payload)

        # ── Retry any queued alerts ───────────────────────────────────────────
        alert_pusher.flush_queue()

        # ── Display overlay ───────────────────────────────────────────────────
        if not no_display:
            _draw_overlay(frame, last_detections, flagged_ids,
                          display_fps, plate_detector.mode)
            cv2.imshow("ANPR — Incident Detection [q to quit]", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print("[Pipeline] Quit signal received.")
                break

    cap.release()
    if not no_display:
        cv2.destroyAllWindows()
    print("[Pipeline] ✅ Done.")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ANPR + Incident Detection Pipeline")
    parser.add_argument("--video",      default=VIDEO_PATH,
                        help="Path to video file or camera index (default: config.VIDEO_PATH)")
    parser.add_argument("--dry-run",    action="store_true",
                        help="Print alerts locally, do not POST to backend")
    parser.add_argument("--no-display", action="store_true",
                        help="Headless mode (no cv2.imshow)")
    args = parser.parse_args()

    main(
        video_path = args.video,
        dry_run    = args.dry_run,
        no_display = args.no_display,
    )
