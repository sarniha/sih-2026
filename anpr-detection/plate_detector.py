"""
plate_detector.py — License Plate Region Detection

Primary:  keremberke/yolov8n-license-plate-detection (pulled via ultralytics)
Fallback: Classical CV — Canny edges + contour filtering by aspect ratio
          (aspect ratio 2:1 – 5.5:1 matches Indian rectangular plates)

The fallback is intentional — no training or fine-tuning is required.
Post-hackathon: replace with a YOLO model fine-tuned on Indian LP dataset
(Roboflow: "Indian number plate") for higher recall on worn/tilted plates.
"""

import cv2
import numpy as np
from typing import List, Tuple

from config import PLATE_CONFIDENCE, PLATE_MODEL_ID


class PlateDetector:
    """
    Detects license plate bounding boxes within a vehicle crop image.

    Usage:
        pd = PlateDetector()
        plates = pd.detect(vehicle_crop_bgr)
        # plates → [(x1, y1, x2, y2, conf), ...]  in crop-relative coords
    """

    def __init__(self):
        self.model  = None
        self.mode   = "yolo"
        self._load_model()

    # ──────────────────────────────────────────────────────────────────────────
    # Model loading
    # ──────────────────────────────────────────────────────────────────────────

    def _load_model(self):
      try:
        from ultralytics import YOLO
        local_path = "models/plate_detector.pt"
        print(f"[PlateDetector] Loading local model: {local_path}")
        self.model = YOLO(local_path)
        self.mode  = "yolo"
        print("[PlateDetector] ✅ YOLO plate detector loaded")
      except Exception as exc:
        print(f"[PlateDetector] ⚠️  YOLO load failed ({exc}). "
              "Falling back to classical CV contour detection.")
        self.model = None
        self.mode  = "classical"

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def detect(self, vehicle_crop: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Args:
            vehicle_crop: BGR image of the vehicle region (already cropped from full frame).

        Returns:
            List of (x1, y1, x2, y2, confidence) in vehicle_crop coordinates,
            sorted by confidence descending.  Empty list if no plate found.
        """
        if vehicle_crop is None or vehicle_crop.size == 0:
            return []

        if self.mode == "yolo":
            return self._detect_yolo(vehicle_crop)
        return self._detect_classical(vehicle_crop)

    # ──────────────────────────────────────────────────────────────────────────
    # YOLO detection
    # ──────────────────────────────────────────────────────────────────────────

    def _detect_yolo(self, img: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        try:
            results = self.model.predict(img, conf=PLATE_CONFIDENCE, verbose=False)
            plates  = []
            boxes   = results[0].boxes
            if boxes is not None:
                for box, conf in zip(boxes.xyxy, boxes.conf):
                    x1, y1, x2, y2 = (int(v) for v in box)
                    plates.append((x1, y1, x2, y2, float(conf)))
            plates.sort(key=lambda p: p[4], reverse=True)
            return plates
        except Exception as exc:
            print(f"[PlateDetector] YOLO inference error: {exc} — switching to classical")
            self.mode = "classical"
            return self._detect_classical(img)

    # ──────────────────────────────────────────────────────────────────────────
    # Classical CV fallback
    # ──────────────────────────────────────────────────────────────────────────

    def _detect_classical(self, img: np.ndarray) -> List[Tuple[int, int, int, int, float]]:
        """
        Heuristic plate finder:
          1. Convert to grayscale, bilateral filter (noise reduction).
          2. Canny edge detection.
          3. Find external contours.
          4. Filter by aspect ratio (2.0 – 5.5) and minimum area.
          5. Return top candidates sorted by area (largest first).

        Confidence is approximated as a function of aspect-ratio closeness to 3.0
        (typical Indian plate aspect ratio).
        """
        h, w = img.shape[:2]
        min_area = (w * h) * 0.003   # at least 0.3% of crop area

        gray      = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blurred   = cv2.bilateralFilter(gray, 11, 17, 17)
        edges     = cv2.Canny(blurred, 30, 200)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        candidates = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area:
                continue
            rx, ry, rw, rh = cv2.boundingRect(cnt)
            if rh == 0:
                continue
            aspect = rw / rh
            if 1.8 <= aspect <= 5.5:
                # Pseudo-confidence: how close aspect ratio is to ideal 3.2
                pseudo_conf = max(0.0, 1.0 - abs(aspect - 3.2) / 3.2)
                candidates.append((rx, ry, rx + rw, ry + rh, round(pseudo_conf, 3)))

        # Sort by descending pseudo-confidence, return top 3
        candidates.sort(key=lambda c: c[4], reverse=True)
        return candidates[:3]
