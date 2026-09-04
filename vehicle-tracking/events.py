import time
import requests
from config import SEND_TO_BACKEND, BACKEND_URL

def build_event(density, avg_speed, avg_confidence, congestion):
    return {
        "event_type": "traffic_density",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "confidence": round(avg_confidence, 2),
        "location": {"lat": None, "lon": None},
        "vehicle_count": density,
        "avg_speed_px_per_frame": round(avg_speed, 2),
        "congestion_level": congestion
    }

def send_event(event):
    print(event)
    if SEND_TO_BACKEND:
        try:
            requests.post(BACKEND_URL, json=event, timeout=2)
        except requests.exceptions.RequestException as e:
            print("Failed to send event:", e)