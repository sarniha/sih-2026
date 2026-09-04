"""
incident_detector.py — Method A: Speed Anomaly Detection

How it works:
  1. Every frame, compute the centroid speed (px/sec) for each tracked vehicle.
  2. Maintain a rolling average over the last SPEED_WINDOW_FRAMES readings.
  3. If the smoothed speed exceeds SPEED_ANOMALY_THRESHOLD, flag the vehicle.
  4. Incident type heuristic:
       - If the vehicle was near-stationary before the spike → "hit_and_run"
       - Otherwise → "rash_driving"
  5. A per-track cooldown prevents the same vehicle being re-flagged within
     INCIDENT_COOLDOWN_SEC seconds.

Post-hackathon improvements:
  - Method B: IoU-based near-miss → collision detection
  - Method C: Fine-tuned CNN/CLIP accident classifier on CADP dataset
"""

import math
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional

from config import (
    INCIDENT_COOLDOWN_SEC,
    SPEED_ANOMALY_THRESHOLD,
    SPEED_WINDOW_FRAMES,
    MAX_PLAUSIBLE_SPEED
)


class IncidentDetector:
    def __init__(self):
        # track_id -> deque of (centroid_x, centroid_y, timestamp)
        self._history: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=SPEED_WINDOW_FRAMES + 1)
        )
        # track_id -> deque of recent px/sec readings for rolling average
        self._speed_history: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=SPEED_WINDOW_FRAMES)
        )
        # track_id -> last flagged timestamp (for cooldown)
        self._last_flagged: Dict[int, float] = {}

    # ──────────────────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────────────────

    def update(self, detections: List[dict]) -> List[dict]:
        """
        Call once per processed frame.

        Args:
            detections: list of dicts produced by VehicleDetector.track():
                {track_id, center_x, center_y, bbox, confidence, class_name}

        Returns:
            List of flagged incidents:
                {track_id, incident_type, speed_px_sec, smoothed_speed_px_sec}
        """
        now = time.time()
        flagged = []

        for det in detections:
            tid   = det["track_id"]
            cx, cy = det["center_x"], det["center_y"]

            # Store position history
            self._history[tid].append((cx, cy, now))

            # Need at least 2 points to compute speed
            if len(self._history[tid]) < 2:
                continue

            prev_x, prev_y, prev_t = self._history[tid][-2]
            dt = now - prev_t
            if dt <= 0:
                continue

            dist   = math.hypot(cx - prev_x, cy - prev_y)
            speed  = dist / dt                              # px / sec
            self._speed_history[tid].append(speed)

            smoothed = self._smoothed_speed(tid)

            if self._is_incident(tid, smoothed, now):
                incident_type = self._classify_incident(tid, smoothed)
                flagged.append({
                    "track_id":             tid,
                    "incident_type":        incident_type,
                    "speed_px_sec":         round(speed, 1),
                    "smoothed_speed_px_sec": round(smoothed, 1),
                })
                self._last_flagged[tid] = now

        # Prune history for tracks no longer visible
        active_ids = {d["track_id"] for d in detections}
        for tid in list(self._history):
            if tid not in active_ids:
                del self._history[tid]
                self._speed_history.pop(tid, None)

        return flagged

    # ──────────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────────

    def _smoothed_speed(self, track_id: int) -> float:
        hist = self._speed_history[track_id]
        if not hist:
            return 0.0
        return sum(hist) / len(hist)

    def _is_incident(self, track_id: int, smoothed: float, now: float) -> bool:
        """True if speed threshold exceeded and not in cooldown."""
        if smoothed>MAX_PLAUSIBLE_SPEED:
            return False
        if smoothed < SPEED_ANOMALY_THRESHOLD:
            return False
        last = self._last_flagged.get(track_id)
        if last is not None and (now - last) < INCIDENT_COOLDOWN_SEC:
            return False
        return True

    def _classify_incident(self, track_id: int, current_smoothed: float) -> str:
        """
        Heuristic: if the vehicle was near-stationary before the speed spike,
        it's more likely a hit-and-run. Otherwise, rash driving.

        'Near-stationary' = average of first half of speed_history < 20 px/s.
        """
        hist = list(self._speed_history[track_id])
        if len(hist) < 2:
            return "rash_driving"

        # First half of the window = "before the spike"
        first_half = hist[: max(1, len(hist) // 2)]
        avg_before = sum(first_half) / len(first_half)

        STATIONARY_THRESHOLD = 20  # px/sec
        if avg_before < STATIONARY_THRESHOLD:
            return "hit_and_run"
        return "rash_driving"
