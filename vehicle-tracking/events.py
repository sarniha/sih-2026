import time
import requests
from config import BACKEND_URL, SERVICE_TOKEN, BUS_ID, TRIP_ID, SEND_TO_BACKEND

def build_event(density, avg_speed, avg_confidence, congestion, lon=None, lat=None, track_id=None):
    severity_map = {"Low": "low", "Medium": "medium", "High": "high"}

    event = {
        "event_type": "traffic",
        "trip_id": TRIP_ID,
        "bus_id": BUS_ID,
        "confidence": round(min(max(avg_confidence, 0.0), 1.0), 3),
        "occurred_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "severity": severity_map.get(congestion, "medium"),
        "object_id": str(track_id) if track_id is not None else f"traf_density_{int(time.time())}"
    }

    if lon is not None and lat is not None:
        event["lon"] = lon
        event["lat"] = lat

    return event

def send_event(event):
    print(event)
    if not SEND_TO_BACKEND:
        return

    try:
        resp = requests.post(
            BACKEND_URL,
            json=event,
            headers={
                "Content-Type": "application/json",
                "X-Service-Token": SERVICE_TOKEN,
            },
            timeout=5,
        )
        if resp.status_code == 201:
            print(f"[OK 201] Event created: id={resp.json()['id']}")
        else:
            print(f"[ERR {resp.status_code}] {resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"[CONN_ERR] {e}")