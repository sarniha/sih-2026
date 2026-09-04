"""
run_pipeline.py — Full ANPR incident pipeline (Step 5 integration)

Wires together:
  1. Vehicle tracking      (YOLOv8 + ByteTrack)
  2. Incident detection    (IncidentDetector — Method A, speed anomaly)
  3. Plate crop + OCR      (PlateDetector + OCRReader)
  4. Alert construction    (alert_builder.build_alert)
  5. Secure push           (AlertPusher)
  6. Evidence frame saving (annotated full frame -> EVIDENCE_DIR)

ASSUMPTIONS MADE (verify these against your real setup):
  - Vehicle tracking is done via direct model.track() calls, matching the
    pattern in test_normal_traffic.py — no separate VehicleTracker wrapper
    class exists.
  - PlateDetector is used as given (hub-pulled "keremberke" model via
    PLATE_MODEL_ID in config.py) — NOT the locally downloaded
    models/plate_detector.pt ("joker5914") that was validated at 75.8%
    confidence earlier. If you intended to use the local file, this needs
    to change (see note near PlateDetector() instantiation below).
  - PROCESS_EVERY_N_FRAMES from config.py is NOT applied to the tracking
    loop here — every frame is processed. Skipping frames would degrade
    ByteTrack's ID continuity and corrupt speed calculations. If you need
    the perf gain, it should be applied to the plate/OCR step only (which
    only runs on flagged incidents anyway, so it's rarely the bottleneck).
"""

import os
import time
import math
import cv2
from collections import defaultdict, deque

from ultralytics import YOLO

from config import (
    MODEL_PATH,
    TRACKER_CONFIG,
    VEHICLE_CLASSES,
    CONFIDENCE_THRESHOLD,
    VIDEO_PATH,
    EVIDENCE_DIR,
    PLATE_DIR,
    DEFAULT_GPS,
    CAMERA_ID,
)

from incident_detector import IncidentDetector
from plate_detector import PlateDetector
from ocr_reader import OCRReader
from alert_builder import build_alert, strip_meta
from alert_pusher import AlertPusher


def xywh_to_corners(cx, cy, w, h):
    """Convert YOLO center-format box to (x1, y1, x2, y2) corner format."""
    x1 = int(cx - w / 2)
    y1 = int(cy - h / 2)
    x2 = int(cx + w / 2)
    y2 = int(cy + h / 2)
    return x1, y1, x2, y2


def run_pipeline(video_path: str = VIDEO_PATH):
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    os.makedirs(PLATE_DIR, exist_ok=True)

    print("[Pipeline] Loading vehicle detection model...")
    vehicle_model = YOLO(MODEL_PATH)

    print("[Pipeline] Loading plate detector...")
    plate_detector = PlateDetector()

    print("[Pipeline] Initializing OCR reader (lazy-loads on first use)...")
    ocr_reader = OCRReader()

    incident_detector = IncidentDetector()
    pusher = AlertPusher()

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"[Pipeline] ERROR: could not open video: {video_path}")
        return

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    print(f"[Pipeline] Video opened. FPS={fps:.1f}")

    frame_num = 0
    incidents_processed = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        results = vehicle_model.track(
            frame,
            classes=VEHICLE_CLASSES,
            conf=CONFIDENCE_THRESHOLD,
            persist=True,
            tracker=TRACKER_CONFIG,
            verbose=False,
        )

        detections = []
        if results[0].boxes.id is not None:
            ids   = results[0].boxes.id.int().tolist()
            boxes = results[0].boxes.xywh.tolist()
            names = results[0].names
            clss  = results[0].boxes.cls.int().tolist()

            for tid, box, cls in zip(ids, boxes, clss):
                detections.append({
                    "track_id":   tid,
                    "center_x":   box[0],
                    "center_y":   box[1],
                    "bbox":       box,          # xywh — raw from YOLO
                    "class_name": names[cls],
                })

        flags = incident_detector.update(detections)

        for flag in flags:
            tid = flag["track_id"]
            det = next((d for d in detections if d["track_id"] == tid), None)
            if det is None:
                # Track vanished same frame it was flagged — skip, can't crop it
                print(f"[Pipeline] ⚠️  Flagged track {tid} has no matching "
                      f"detection this frame — skipping (track likely lost)")
                continue

            print(f"[Pipeline] 🚨 Incident detected | track_id={tid} "
                  f"type={flag['incident_type']} "
                  f"speed={flag['smoothed_speed_px_sec']:.1f}px/s "
                  f"frame={frame_num}")

            cx, cy, w, h = det["bbox"]
            x1, y1, x2, y2 = xywh_to_corners(cx, cy, w, h)

            # Clip to frame bounds before cropping
            fh, fw = frame.shape[:2]
            cx1, cy1 = max(0, x1), max(0, y1)
            cx2, cy2 = min(fw, x2), min(fh, y2)
            vehicle_crop = frame[cy1:cy2, cx1:cx2]

            plate_text_raw   = None
            plate_conf       = 0.0
            plate_text_clean = None

            if vehicle_crop.size > 0:
                plate_boxes = plate_detector.detect(vehicle_crop)
                if plate_boxes:
                    px1, py1, px2, py2, pconf = plate_boxes[0]  # highest confidence
                    plate_crop = vehicle_crop[py1:py2, px1:px2]

                    if plate_crop.size > 0:
                        plate_crop_path = os.path.join(
                            PLATE_DIR, f"plate_track{tid}_frame{frame_num}.jpg"
                        )
                        cv2.imwrite(plate_crop_path, plate_crop)

                        plate_text_raw, plate_conf = ocr_reader.read_plate(plate_crop)
                        plate_text_clean = ocr_reader.clean_plate(plate_text_raw)

                        print(f"[Pipeline]   📋 Plate cropped -> OCR raw="
                              f"'{plate_text_raw}' clean='{plate_text_clean}' "
                              f"conf={plate_conf:.3f}")
                    else:
                        print("[Pipeline]   ⚠️  Plate box detected but crop was empty")
                else:
                    print("[Pipeline]   ⚠️  No plate detected in vehicle crop")
            else:
                print("[Pipeline]   ⚠️  Vehicle crop was empty — bbox may be off-frame")

            # Save evidence frame (full annotated frame, not just the crop)
            evidence_filename = f"evidence_track{tid}_frame{frame_num}.jpg"
            evidence_path = os.path.join(EVIDENCE_DIR, evidence_filename)
            annotated = frame.copy()
            cv2.rectangle(annotated, (cx1, cy1), (cx2, cy2), (0, 0, 255), 3)
            cv2.putText(
                annotated, f"track={tid} {flag['incident_type']}",
                (cx1, max(0, cy1 - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 0, 255), 2,
            )
            cv2.imwrite(evidence_path, annotated)

            alert = build_alert(
                track_id=tid,
                incident_type=flag["incident_type"],
                plate_text=plate_text_clean,
                plate_conf=plate_conf,
                raw_plate_text=plate_text_raw,
                vehicle_bbox=(x1, y1, x2, y2),
                vehicle_class=det["class_name"],
                evidence_url=evidence_path,
                gps=DEFAULT_GPS,
                frame_num=frame_num,
                fps=fps,
                speed_px_sec=flag["smoothed_speed_px_sec"],
            )
            print(f"[Pipeline]   📦 Alert built | event_type={alert['event_type']} "
                  f"severity={alert['severity']}")

            clean_payload = strip_meta(alert)
            success = pusher.push(clean_payload)
            print(f"[Pipeline]   📡 Alert push {'succeeded' if success else 'FAILED (queued)'}")

            incidents_processed += 1

        # Retry any previously failed pushes (throttled internally to every 5s)
        pusher.flush_queue()

        frame_num += 1

    cap.release()
    print(f"\n[Pipeline] Done. Frames processed: {frame_num}. "
          f"Incidents handled: {incidents_processed}. "
          f"Still queued for retry: {len(pusher._retry_queue)}")


if __name__ == "__main__":
    run_pipeline("models/staged_incident_clip.mp4")