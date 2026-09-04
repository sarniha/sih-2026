import math
import time
from config import ZONE, DENSITY_LOW_MAX, DENSITY_MEDIUM_MAX, SPEED_JAM_THRESHOLD

class DensityTracker:
    def __init__(self):
        self.previous_positions = {}  # track_id -> (x, y, timestamp)

    def _is_inside_zone(self, x, y):
        x1, y1, x2, y2 = ZONE
        return x1 <= x <= x2 and y1 <= y <= y2

    def update(self, detections):
        density = 0
        speeds_in_zone = []
        confidences_in_zone = []
        active_ids = set()
        now = time.time()

        for det in detections:
            track_id = det["track_id"]
            cx, cy = det["center_x"], det["center_y"]
            active_ids.add(track_id)
            inside = self._is_inside_zone(cx, cy)

            speed = 0
            if track_id in self.previous_positions:
                prev_x, prev_y, prev_time = self.previous_positions[track_id]
                elapsed = now - prev_time
                if elapsed > 0:
                    distance = math.sqrt((cx - prev_x) ** 2 + (cy - prev_y) ** 2)
                    speed = distance / elapsed  # pixels per second

            if inside:
                density += 1
                speeds_in_zone.append(speed)
                confidences_in_zone.append(det["confidence"])

            self.previous_positions[track_id] = (cx, cy, now)

        self.previous_positions = {
            tid: pos for tid, pos in self.previous_positions.items() if tid in active_ids
        }

        avg_speed = sum(speeds_in_zone) / len(speeds_in_zone) if speeds_in_zone else 0
        avg_confidence = sum(confidences_in_zone) / len(confidences_in_zone) if confidences_in_zone else 0
        congestion = self._get_congestion_label(density, avg_speed)

        return density, avg_speed, avg_confidence, congestion

    def _get_congestion_label(self, density, avg_speed):
        if density <= DENSITY_LOW_MAX:
            return "Low"
        elif density <= DENSITY_MEDIUM_MAX:
            return "High" if avg_speed < SPEED_JAM_THRESHOLD else "Medium"
        else:
            return "High"