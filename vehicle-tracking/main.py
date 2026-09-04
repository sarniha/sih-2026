import cv2
import time

from config import ZONE, VIDEO_PATH, EMIT_INTERVAL_SECONDS, PROCESS_EVERY_N_FRAMES
from detector import VehicleDetector
from density import DensityTracker
from events import build_event, send_event

def draw_detections(frame, detections):
    for det in detections:
        cx, cy = det["center_x"], det["center_y"]
        track_id = det["track_id"]
        cv2.circle(frame, (cx, cy), 4, (0, 255, 0), -1)
        cv2.putText(frame, f"ID {track_id}", (cx - 10, cy - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

def is_inside_zone(x, y):
    x1, y1, x2, y2 = ZONE
    return x1 <= x <= x2 and y1 <= y <= y2

def main():
    detector = VehicleDetector()
    density_tracker = DensityTracker()

    cap = cv2.VideoCapture(VIDEO_PATH)
    if not cap.isOpened():
        raise IOError(f"Could not open video source: {VIDEO_PATH}")

    last_emit_time = time.time()
    prev_frame_time = time.time()
    frame_count = 0

    last_detections = []
    density, avg_speed, avg_confidence, congestion = 0, 0, 0, "Low"

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        if frame_count % PROCESS_EVERY_N_FRAMES == 0:
            last_detections, _ = detector.track(frame)
            density, avg_speed, avg_confidence, congestion = density_tracker.update(last_detections)

        draw_detections(frame, last_detections)

        now = time.time()
        fps = 1 / (now - prev_frame_time) if now != prev_frame_time else 0
        prev_frame_time = now

        x1, y1, x2, y2 = ZONE
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 2)
        cv2.putText(frame, f"Density: {density}  Congestion: {congestion}",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv2.putText(frame, f"FPS: {fps:.1f}",
                    (20, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Send one event per vehicle currently in the zone, on the emit interval
        if time.time() - last_emit_time >= EMIT_INTERVAL_SECONDS:
            for det in last_detections:
                if is_inside_zone(det["center_x"], det["center_y"]):
                    event = build_event(
                        density=density,
                        avg_speed=avg_speed,
                        avg_confidence=det["confidence"],
                        congestion=congestion,
                        track_id=det["track_id"]
                    )
                    send_event(event)
            last_emit_time = time.time()

        cv2.imshow("Traffic Intelligence", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()