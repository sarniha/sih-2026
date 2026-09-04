"""
detector.py — Modular YOLOv8 + ByteTrack road defect detector with temporal confirmation.
"""

from typing import Dict, List, Optional, Tuple, Any
from ultralytics import YOLO
import cv2

from config import (
    MODEL_PATH,
    TRACKER_CONFIG,
    CONFIDENCE_THRESHOLD,
    INPUT_SIZE,
    MIN_HITS_CONFIRMATION,
    MAX_AGE_FRAMES,
)
from severity import compute_severity

CLASS_DISPLAY = {
    "D00": "Longitudinal Crack",
    "D10": "Transverse Crack",
    "D20": "Alligator Crack",
    "D40": "Pothole",
    "Repair": "Road Repair",
    "pothole": "Pothole",
    "crack": "Road Crack",
    "damaged_road": "Damaged Road",
    "waterlogging": "Waterlogging",
}


class DefectTrackState:
    """Tracks confirmation state for a single detected defect across frames."""

    def __init__(self, track_id: int, bbox: list, conf: float, class_name: str, frame_num: int, frame_img=None):
        self.id = track_id
        self.class_name = class_name
        self.hit_frames: List[int] = [frame_num]
        self.last_seen_frame = frame_num
        self.best_conf = conf
        self.best_bbox = bbox
        self.best_frame_img = frame_img.copy() if frame_img is not None else None
        self.confirmed = False
        self.emitted = False

    def update(self, bbox: list, conf: float, class_name: str, frame_num: int, frame_img=None):
        self.hit_frames.append(frame_num)
        self.last_seen_frame = frame_num
        if conf > self.best_conf:
            self.best_conf = conf
            self.best_bbox = bbox
            self.class_name = class_name
            if frame_img is not None:
                self.best_frame_img = frame_img.copy()

    def should_confirm(self, min_hits: int = MIN_HITS_CONFIRMATION) -> bool:
        return len(self.hit_frames) >= min_hits


class RoadDefectDetector:
    """High-level detector and tracker for road surface defects."""

    def __init__(
        self,
        model_path: str = MODEL_PATH,
        conf_threshold: float = CONFIDENCE_THRESHOLD,
        min_hits: int = MIN_HITS_CONFIRMATION,
        imgsz: int = INPUT_SIZE,
    ):
        self.model = YOLO(model_path)
        self.conf_threshold = conf_threshold
        self.min_hits = min_hits
        self.imgsz = imgsz
        self.tracks: Dict[int, DefectTrackState] = {}

    def process_frame(
        self,
        frame,
        frame_num: int,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Runs YOLO tracking on the frame.
        Returns:
            active_detections: All currently detected defects in this frame.
            newly_confirmed: Defects that crossed the temporal confirmation threshold in this frame.
        """
        results = self.model.track(
            frame,
            persist=True,
            tracker=TRACKER_CONFIG,
            conf=self.conf_threshold,
            imgsz=self.imgsz,
            verbose=False,
        )

        h, w = frame.shape[:2]
        active_detections = []
        newly_confirmed = []
        current_frame_track_ids = set()

        boxes = results[0].boxes
        if boxes is not None and boxes.id is not None:
            for box, track_id_t, conf_t, cls_id_t in zip(
                boxes.xyxy, boxes.id, boxes.conf, boxes.cls
            ):
                track_id = int(track_id_t.item())
                conf = float(conf_t.item())
                cls_id = int(cls_id_t.item())
                raw_class_name = self.model.names.get(cls_id, "pothole")
                bbox = [float(v) for v in box.tolist()]

                current_frame_track_ids.add(track_id)
                severity_label, severity_score = compute_severity(
                    bbox, conf, w, h, class_name=raw_class_name
                )

                if track_id not in self.tracks:
                    self.tracks[track_id] = DefectTrackState(
                        track_id, bbox, conf, raw_class_name, frame_num, frame
                    )
                else:
                    self.tracks[track_id].update(
                        bbox, conf, raw_class_name, frame_num, frame
                    )

                trk = self.tracks[track_id]

                active_detections.append({
                    "track_id": track_id,
                    "bbox": bbox,
                    "confidence": conf,
                    "class_name": raw_class_name,
                    "display_name": CLASS_DISPLAY.get(raw_class_name, raw_class_name),
                    "severity": severity_label,
                    "severity_score": severity_score,
                    "confirmed": trk.confirmed,
                })

                # Check for first-time confirmation
                if not trk.confirmed and trk.should_confirm(self.min_hits):
                    trk.confirmed = True
                    newly_confirmed.append({
                        "track_id": track_id,
                        "bbox": trk.best_bbox,
                        "confidence": trk.best_conf,
                        "class_name": trk.class_name,
                        "display_name": CLASS_DISPLAY.get(trk.class_name, trk.class_name),
                        "severity": severity_label,
                        "severity_score": severity_score,
                        "frame_img": trk.best_frame_img if trk.best_frame_img is not None else frame,
                        "frame_num": frame_num,
                    })

        # Purge stale tracks beyond MAX_AGE_FRAMES
        stale_ids = [
            tid for tid, trk in self.tracks.items()
            if frame_num - trk.last_seen_frame > MAX_AGE_FRAMES
        ]
        for tid in stale_ids:
            del self.tracks[tid]

        return active_detections, newly_confirmed
