import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.db.session import SessionLocal
from app.models import Bus, Trip

client = TestClient(app)


def setup_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="WS Test Bus", registration_number=f"BR01W{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="ws_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def test_websocket_live_event_and_incident_connection():
    # Verify WebSocket connection acceptance for events feed
    with client.websocket_connect("/api/v1/ws/events") as websocket:
        websocket.send_text("ping")

    # Verify WebSocket connection acceptance for incidents feed
    with client.websocket_connect("/api/v1/ws/incidents") as websocket:
        websocket.send_text("ping")
