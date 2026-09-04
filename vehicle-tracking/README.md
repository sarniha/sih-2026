# Vehicle Tracking & Traffic Intelligence Module

Owned by: P2

Takes bus-camera footage and produces vehicle detections, persistent track IDs,
zone-based density, speed estimation, and a congestion score — output as
normalized JSON events for the backend to ingest.

## Setup

pip install -r requirements.txt

## Run

Place a test video as `traffic.mp4` in this folder (or update `VIDEO_PATH` in
`config.py`), then:

python main.py

## Files

- `config.py` — all tunable settings (model, zone, thresholds)
- `detector.py` — YOLOv8 + ByteTrack detection/tracking wrapper
- `density.py` — zone-occupancy density, speed estimation, congestion scoring
- `events.py` — builds and sends normalized traffic events
- `main.py` — runs the full pipeline on a video

## Output event shape

{
  "event_type": "traffic_density",
  "timestamp": "...",
  "confidence": 0.85,
  "location": {"lat": null, "lon": null},
  "vehicle_count": 6,
  "avg_speed_px_per_frame": 12.4,
  "congestion_level": "Medium"
}

## Notes

- ZONE in config.py is tuned per camera angle/resolution — retune using
  zone_preview logic when testing on new footage.
- SEND_TO_BACKEND is False by default until the real FastAPI endpoint is live.