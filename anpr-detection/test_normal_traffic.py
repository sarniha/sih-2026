# test_normal_traffic.py
from ultralytics import YOLO
import cv2
from incident_detector import IncidentDetector

model = YOLO("yolov8n.pt")
video_path = "models/staged_incident_clip.mp4"
cap = cv2.VideoCapture(video_path)

detector = IncidentDetector()
all_flags = []
frame_num = 0
total_detections = 0

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    results = model.track(frame, classes=[2,3,5,7], persist=True, tracker="bytetrack.yaml", verbose=False)

    detections = []
    if results[0].boxes.id is not None:
        ids = results[0].boxes.id.int().tolist()
        boxes = results[0].boxes.xywh.tolist()
        confs = results[0].boxes.conf.tolist()
        clss = results[0].boxes.cls.int().tolist()
        names = results[0].names

        for tid, box, conf, cls in zip(ids, boxes, confs, clss):
            cx, cy = box[0], box[1]
            detections.append({
                "track_id": tid,
                "center_x": cx,
                "center_y": cy,
                "bbox": box,
                "confidence": conf,
                "class_name": names[cls],
            })
            total_detections += 1

    flags = detector.update(detections)
    for f in flags:
        f["frame_num"] = frame_num
        all_flags.append(f)

    frame_num += 1

cap.release()

print(f"Total frames: {frame_num}")
print(f"Total detections: {total_detections}")
print(f"Total incidents flagged: {len(all_flags)}")
print()
for f in all_flags:
    print(f)