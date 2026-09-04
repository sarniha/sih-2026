import uuid
from datetime import datetime, timezone

from app.core.config import settings
from app.db.session import SessionLocal
from app.main import app
from app.models import Bus, Trip
from fastapi.testclient import TestClient

client = TestClient(app)


def setup_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="Auth Test Bus", registration_number=f"BR01A{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="auth_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def build_payload(bus_id, trip_id):
    return {
        "event_type": "pothole",
        "trip_id": str(trip_id),
        "bus_id": str(bus_id),
        "confidence": 0.85,
        "lon": 85.1330,
        "lat": 25.5970,
        "occurred_at": "2026-01-01T00:00:00Z",
        "severity": "low",
    }


def test_post_event_without_token_returns_401():
    bus_id, trip_id = setup_bus_and_trip()
    resp = client.post("/api/v1/events", json=build_payload(bus_id, trip_id))
    assert resp.status_code == 401


def test_post_event_with_wrong_token_returns_401():
    bus_id, trip_id = setup_bus_and_trip()
    resp = client.post(
        "/api/v1/events",
        json=build_payload(bus_id, trip_id),
        headers={"X-Service-Token": "definitely-not-the-real-token"},
    )
    assert resp.status_code == 401


def test_post_event_with_correct_token_is_not_blocked_by_auth():
    bus_id, trip_id = setup_bus_and_trip()
    resp = client.post(
        "/api/v1/events",
        json=build_payload(bus_id, trip_id),
        headers={"X-Service-Token": settings.service_token},
    )
    assert resp.status_code == 201


def test_patch_incident_without_token_returns_401():
    resp = client.patch(
        "/api/v1/incidents/00000000-0000-0000-0000-000000000000",
        json={"status": "under_review"},
    )
    assert resp.status_code == 401