# test_timing.py
import time
from alert_builder import build_alert, strip_meta
from alert_pusher import AlertPusher
from config import DEFAULT_GPS

alert = build_alert(
    track_id=1000, incident_type="rash_driving", plate_text="DL01XY9999",
    plate_conf=0.7, raw_plate_text="DL01XY9999", vehicle_bbox=(100,100,300,300),
    vehicle_class="car", evidence_url=None, gps=DEFAULT_GPS,
    frame_num=200, fps=30, speed_px_sec=700.0,
)
payload = strip_meta(alert)

pusher = AlertPusher()
start = time.time()
result = pusher.push(payload)
elapsed = time.time() - start
print(f"\nElapsed: {elapsed:.2f}s | Success: {result}")