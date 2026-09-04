from ultralytics import YOLO
from config import MODEL_PATH, TRACKER_CONFIG, VEHICLE_CLASSES, CONFIDENCE_THRESHOLD, INPUT_SIZE

class VehicleDetector:
    def __init__(self):
        self.model = YOLO(MODEL_PATH)

    def track(self, frame):
        results = self.model.track(
            frame,
            classes=VEHICLE_CLASSES,
            persist=True,
            tracker=TRACKER_CONFIG,
            conf=CONFIDENCE_THRESHOLD,
            imgsz=INPUT_SIZE,
            verbose=False
        )

        detections = []
        boxes = results[0].boxes
        if boxes is not None and boxes.id is not None:
            for box, track_id, conf in zip(boxes.xyxy, boxes.id, boxes.conf):
                x1, y1, x2, y2 = box
                detections.append({
                    "track_id": int(track_id),
                    "center_x": int((x1 + x2) / 2),
                    "center_y": int((y1 + y2) / 2),
                    "confidence": float(conf)
                })

        return detections, results[0]