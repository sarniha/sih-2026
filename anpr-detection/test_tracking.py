from ultralytics import YOLO
import cv2

model = YOLO("yolov8n.pt")
video_path = "models/test_clip.mp4"
cap = cv2.VideoCapture(video_path)

fourcc = cv2.VideoWriter_fourcc(*'XVID')
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
out = cv2.VideoWriter('models/tracked_output.avi', fourcc, fps, (w, h))

frame_count = 0
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break
    results = model.track(frame, classes=[2,3,5,7], persist=True, tracker="bytetrack.yaml", verbose=False)
    annotated = results[0].plot()
    out.write(annotated)
    frame_count += 1

cap.release()
out.release()
print(f"Wrote {frame_count} frames to models/tracked_output.avi")