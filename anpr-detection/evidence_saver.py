"""
evidence_saver.py — Save annotated evidence frames to disk

Saves two files per incident:
  1. Full annotated frame  → evidence_incidents/incident_{track_id}_{plate}_{ts}.jpg
  2. Plate crop            → plate_crops/plate_{track_id}_{ts}.jpg

The evidence_url returned is the relative path routed through the backend's
existing /static/ mount (FastAPI StaticFiles), so the frontend can load it
directly as http://backend-host/static/evidence_incidents/...jpg.

The backend's evidence_service.py already calls ensure_evidence_dir() on
startup for the backend's own static/evidence/ folder. This module manages
its own output dirs and creates them on first use.
"""

import os
import cv2
import time
import numpy as np
from typing import Optional, Tuple


class EvidenceSaver:
    """Annotates and saves evidence frames for incident alerts."""

    # Annotation colours (BGR)
    VEHICLE_COLOUR = (0,  255,   0)     # green  — vehicle bbox
    PLATE_COLOUR   = (255, 255,  0)     # cyan   — plate bbox
    TEXT_COLOUR    = (0,  255, 255)     # yellow — plate text overlay
    WARN_COLOUR    = (0,   0,  255)     # red    — "INCIDENT" label

    def __init__(self, evidence_dir: str = "evidence_incidents",
                 plate_dir: str = "plate_crops"):
        self.evidence_dir = evidence_dir
        self.plate_dir    = plate_dir
        os.makedirs(evidence_dir, exist_ok=True)
        os.makedirs(plate_dir,    exist_ok=True)

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def save(
        self,
        frame:        np.ndarray,
        track_id:     int,
        incident_type: str,
        plate_text:   Optional[str],
        vehicle_bbox: Tuple[int, int, int, int],   # (x1, y1, x2, y2) in full frame
        plate_bbox:   Optional[Tuple[int, int, int, int]] = None,  # full-frame coords
        plate_img:    Optional[np.ndarray] = None,
    ) -> str:
        """
        Annotate frame and write to disk.

        Returns:
            evidence_url — relative URL path for the backend event payload
                          e.g. "evidence_incidents/incident_42_MH12AB1234_1725466245.jpg"
        """
        ts  = int(time.time())
        tag = plate_text.replace(" ", "") if plate_text else "UNKNOWN"
        filename = f"incident_{track_id}_{tag}_{ts}.jpg"
        filepath = os.path.join(self.evidence_dir, filename)

        annotated = self._annotate(frame.copy(), track_id, incident_type,
                                   plate_text, vehicle_bbox, plate_bbox)
        cv2.imwrite(filepath, annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])

        # Save standalone plate crop if we have one
        if plate_img is not None and plate_img.size > 0:
            plate_filename = f"plate_{track_id}_{ts}.jpg"
            cv2.imwrite(os.path.join(self.plate_dir, plate_filename), plate_img,
                        [cv2.IMWRITE_JPEG_QUALITY, 95])

        # Return the relative path that maps to /static/ on the backend
        return f"evidence_incidents/{filename}"

    # ──────────────────────────────────────────────────────────────────────────
    # Annotation helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _annotate(
        self,
        img:          np.ndarray,
        track_id:     int,
        incident_type: str,
        plate_text:   Optional[str],
        vehicle_bbox: Tuple,
        plate_bbox:   Optional[Tuple],
    ) -> np.ndarray:
        x1, y1, x2, y2 = vehicle_bbox

        # Vehicle bounding box
        cv2.rectangle(img, (x1, y1), (x2, y2), self.VEHICLE_COLOUR, 2)
        cv2.putText(img, f"ID {track_id}", (x1, y1 - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.VEHICLE_COLOUR, 2)

        # Plate bounding box (drawn on full frame coords)
        if plate_bbox:
            px1, py1, px2, py2 = plate_bbox
            cv2.rectangle(img, (px1, py1), (px2, py2), self.PLATE_COLOUR, 2)

        # Plate text label
        label = plate_text if plate_text else "PLATE UNREAD"
        cv2.putText(img, label, (x1, y2 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.TEXT_COLOUR, 2)

        # Incident type banner (top-left)
        banner = f"⚠ {incident_type.upper().replace('_', ' ')}"
        cv2.putText(img, banner, (10, 32),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, self.WARN_COLOUR, 3)

        return img
