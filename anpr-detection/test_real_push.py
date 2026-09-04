# test_real_push.py
from alert_builder import build_alert, strip_meta
from alert_pusher import AlertPusher
from config import DEFAULT_GPS
import json

# Build a realistic fake alert using your real build_alert()
alert = build_alert(
    track_id=999,
    incident_type="hit_and_run",
    plate_text="DL01AB1234",
    plate_conf=0.85,
    raw_plate_text="DL O1 AB1234",
    vehicle_bbox=(320, 280, 640, 480),   # x1, y1, x2, y2 — placeholder for now
    vehicle_class="car",
    evidence_url=None,
    gps=DEFAULT_GPS,
    frame_num=150,
    fps=30,
    speed_px_sec=850.0,
)

print("Full payload (with _meta):")
print(json.dumps(alert, indent=2, default=str))

clean_payload = strip_meta(alert)
print("\nPayload being sent to backend (meta stripped):")
print(json.dumps(clean_payload, indent=2, default=str))

pusher = AlertPusher()
result = pusher.push(clean_payload)
print("\nPush returned:", result)