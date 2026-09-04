# test_pusher_dryrun.py
from alert_pusher import AlertPusher

pusher = AlertPusher()
fake_alert = {"event_type": "hit_run", "plate_text": "DL01AB1234", "confidence": 0.9}
result = pusher.push(fake_alert)
print("Push returned:", result)