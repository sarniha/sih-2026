"""
gps_utils.py — lightweight GPS track loader and interpolator.
Accepts a CSV with columns: elapsed_sec, lat, lon
"""

import csv
import math
from typing import Optional, Dict, List, Tuple


class GPSTrack:
    """Load a GPS track CSV and interpolate coordinates for any elapsed time."""

    def __init__(self, csv_path: Optional[str]):
        self._waypoints: List[Tuple[float, float, float]] = []  # (elapsed_sec, lat, lon)
        if csv_path is None:
            return
        try:
            with open(csv_path, newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self._waypoints.append((
                        float(row["elapsed_sec"]),
                        float(row["lat"]),
                        float(row["lon"]),
                    ))
            self._waypoints.sort(key=lambda r: r[0])   # ensure chronological order
        except Exception as e:
            print(f"[GPSTrack Warning] Failed to load GPS track from {csv_path}: {e}")

    def available(self) -> bool:
        return len(self._waypoints) >= 2

    def at(self, frame_num: int, fps: float) -> Optional[Dict[str, float]]:
        """Return interpolated {lat, lon, elapsed_sec} for the given frame, or None."""
        if not self.available():
            return None

        elapsed = frame_num / max(fps, 1.0)

        # Before the first waypoint -> clamp to first
        if elapsed <= self._waypoints[0][0]:
            _, lat, lon = self._waypoints[0]
            return {"lat": round(lat, 7), "lon": round(lon, 7), "elapsed_sec": round(elapsed, 3)}

        # After the last waypoint -> clamp to last
        if elapsed >= self._waypoints[-1][0]:
            _, lat, lon = self._waypoints[-1]
            return {"lat": round(lat, 7), "lon": round(lon, 7), "elapsed_sec": round(elapsed, 3)}

        # Binary search for the bracketing waypoints
        lo, hi = 0, len(self._waypoints) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if self._waypoints[mid][0] <= elapsed:
                lo = mid
            else:
                hi = mid

        t0, lat0, lon0 = self._waypoints[lo]
        t1, lat1, lon1 = self._waypoints[hi]
        denom = (t1 - t0)
        alpha = (elapsed - t0) / denom if denom > 0 else 0.0

        lat = lat0 + alpha * (lat1 - lat0)
        lon = lon0 + alpha * (lon1 - lon0)
        return {"lat": round(lat, 7), "lon": round(lon, 7), "elapsed_sec": round(elapsed, 3)}

    @staticmethod
    def haversine_m(loc1: Dict[str, float], loc2: Dict[str, float]) -> float:
        """Great-circle distance in metres between two {lat, lon} dicts."""
        R = 6_371_000
        phi1, phi2 = math.radians(loc1["lat"]), math.radians(loc2["lat"])
        dphi  = math.radians(loc2["lat"] - loc1["lat"])
        dlam  = math.radians(loc2["lon"] - loc1["lon"])
        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
        return 2 * R * math.asin(math.sqrt(max(0.0, min(1.0, a))))
