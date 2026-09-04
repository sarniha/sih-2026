# test_pusher_retry.py
from alert_pusher import AlertPusher

# Point at a port nothing is listening on, so this fails on purpose
pusher = AlertPusher(api_url="http://localhost:9999/nonexistent")

fake_alert = {"event_type": "hit_run", "plate_text": "DL01AB1234", "confidence": 0.9}
result = pusher.push(fake_alert)

print("Push returned:", result)
print("Queue size:", len(pusher._retry_queue))