# test_speed_distribution.py
from ultralytics import YOLO
import cv2, math, statistics, time
from collections import defaultdict, deque

SPEED_WINDOW_FRAMES = 5  # must match config.py

model = YOLO("yolov8n.pt")
video_path = "models/test_clip.mp4"
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
print(f"Video FPS: {fps}")

history = defaultdict(lambda: deque(maxlen=2))          # tid -> (cx, cy, t)
speed_history = defaultdict(lambda: deque(maxlen=SPEED_WINDOW_FRAMES))
all_smoothed_speeds = []

frame_num = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Use frame_num / fps as the timestamp instead of wall-clock time,
    # so this matches offline processing consistently regardless of
    # how fast this script actually runs on your machine.
    t = frame_num / fps

    results = model.track(frame, classes=[2,3,5,7], persist=True, tracker="bytetrack.yaml", verbose=False)
    if results[0].boxes.id is not None:
        ids = results[0].boxes.id.int().tolist()
        boxes = results[0].boxes.xywh.tolist()
        for tid, box in zip(ids, boxes):
            cx, cy = box[0], box[1]
            history[tid].append((cx, cy, t))

            if len(history[tid]) == 2:
                (px, py, pt), (cx2, cy2, ct) = history[tid]
                dt = ct - pt
                if dt > 0:
                    speed = math.hypot(cx2 - px, cy2 - py) / dt   # px/sec
                    speed_history[tid].append(speed)
                    smoothed = sum(speed_history[tid]) / len(speed_history[tid])
                    all_smoothed_speeds.append(smoothed)

    frame_num += 1

cap.release()
all_smoothed_speeds.sort()
print(f"Total samples: {len(all_smoothed_speeds)}")
print(f"Median: {statistics.median(all_smoothed_speeds):.1f}")
print(f"90th percentile: {all_smoothed_speeds[int(len(all_smoothed_speeds)*0.90)]:.1f}")
print(f"95th percentile: {all_smoothed_speeds[int(len(all_smoothed_speeds)*0.95)]:.1f}")
print(f"99th percentile: {all_smoothed_speeds[int(len(all_smoothed_speeds)*0.99)]:.1f}")
print(f"Max: {all_smoothed_speeds[-1]:.1f}")