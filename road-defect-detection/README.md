# Road Defect & Pothole Detection Module (`road-defect-detection/`)

AI-powered edge sensing module for urban public transit buses (SIH 2026). Transforms bus-mounted cameras into real-time mobile road distress inspection units.

---

## 1. Overview & Capabilities

* **Multi-Class Distress Sensing**: Detects potholes, alligator cracks, longitudinal cracks, transverse cracks, and road surface damage using custom YOLOv8 models.
* **Temporal Confirmation (Anti-False-Positive)**: Tracks candidates across frames via ByteTrack. Alerts trigger only when a defect is verified across $\ge 3$ frames within a temporal sliding window, eliminating transient visual artifacts.
* **Geometric Severity Classification**: Analyzes defect bounding-box area relative to roadway geometry and model confidence to categorize severity as `low`, `medium`, or `high`.
* **GPS Telemetry Geo-Referencing**: Interpolates GPS coordinates (latitude, longitude, speed, heading) matching exact video detection timestamps.
* **Multi-Camera Orchestration**: Ingests synchronized feeds from front windshield, rear, and side cameras, applying spatial Haversine clustering to deduplicate cross-camera detections within 10 meters.
* **Optical Evidence Snapshotting**: Automatically crops and annotates high-resolution evidence frames, storing them for operator triage and incident verification.
* **Live Command Center Sync**: Formats payloads adhering strictly to the backend `PotholeEvent` schema and streams events live over HTTP REST with `X-Service-Token` authentication.

---

## 2. Directory Structure

```
road-defect-detection/
├── config.py             # Centralized module configuration and thresholds
├── detector.py           # YOLOv8 + ByteTrack detection and temporal tracking
├── severity.py           # Road distress severity estimator (low, medium, high)
├── gps_utils.py          # Temporal GPS interpolator and Haversine distance calculator
├── events.py             # Event constructor, evidence exporter, and backend dispatcher
├── dedup.py              # Spatial-temporal Haversine clustering and deduplication
├── multi_camera.py       # Multi-stream concurrent processor (front, rear, sides)
├── video_writer.py       # HUD visualizer overlaying metrics and bounding boxes
├── main.py               # Main CLI executable for single-camera or live streams
├── run_pipeline.sh       # Convenience test script
├── requirements.txt      # Module Python dependencies
├── weights/
│   └── best.pt           # Trained YOLOv8 road defect weights (5.9 MB)
├── data/
│   ├── sample_gps.csv    # Sample GPS track
│   └── synthetic_test.mp4# Sample verification video
└── evidence/             # Local storage for captured defect snapshots
```

---

## 3. Quickstart Guide

### A. Installation
```bash
cd road-defect-detection
pip install -r requirements.txt
```

### B. Run Pipeline on Sample Video
```bash
# Process sample video and emit events to backend
python main.py \
  --video data/synthetic_test.mp4 \
  --gps data/sample_gps.csv \
  --send-backend

# Or run with annotated video HUD output
python main.py \
  --video data/synthetic_test.mp4 \
  --gps data/sample_gps.csv \
  --outvid annotated_output.mp4 \
  --out events.json
```

### C. Run on Multi-Camera Bus Setup
```bash
python multi_camera.py \
  --cameras front=data/synthetic_test.mp4 rear=data/synthetic_test.mp4 \
  --gps data/sample_gps.csv \
  --send-backend
```

### D. Run on Live Webcam / RTSP Camera
```bash
python main.py --video 0 --send-backend
# Or RTSP IP camera:
python main.py --video "rtsp://admin:pass@192.168.1.100:554/stream" --send-backend
```

---

## 4. Backend Event Payload Specification

Events emitted to `POST /api/v1/events` adhere to the `PotholeEvent` schema:

```json
{
  "event_type": "pothole",
  "trip_id": "004b1d9f-d0b8-471d-9f5d-c14a404a4c5a",
  "bus_id": "4af85ce8-b9b9-4a7c-963d-a5eaceb5e236",
  "camera_id": null,
  "object_id": "pothole_4",
  "confidence": 0.874,
  "occurred_at": "2026-09-05T00:00:00Z",
  "severity": "high",
  "bbox": {
    "x": 210,
    "y": 380,
    "w": 180,
    "h": 95
  },
  "lon": 77.058312,
  "lat": 28.552145,
  "evidence_url": "/static/evidence/defect_pothole_4_1788540000_abc123.jpg",
  "metadata": {
    "defect_class": "pothole",
    "camera_position": "windshield_front",
    "detected_by": "road-defect-detection-edge"
  }
}
```

---

## 5. Configuration Options (`config.py`)

Environment variables can override default settings:

| Variable | Default | Description |
|---|---|---|
| `BACKEND_URL` | `http://localhost:8000/api/v1/events` | Event ingestion endpoint |
| `SERVICE_TOKEN` | `smartbus_secret_token_dev_2026` | Service auth token |
| `BUS_ID` | Seeded UUID | Bus entity identifier |
| `TRIP_ID` | Seeded UUID | Active trip identifier |
| `CONFIDENCE_THRESHOLD` | `0.25` | Minimum YOLO detection confidence |
| `MIN_HITS_CONFIRMATION` | `3` | Consecutive tracked frames to confirm defect |
| `SEND_TO_BACKEND` | `true` | Flag to emit HTTP POST events |
