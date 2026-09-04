import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings

from app.db.session import SessionLocal
from app.models import Bus, Trip

client = TestClient(app)
AUTH_HEADERS = {"X-Service-Token": settings.service_token}


def setup_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="Incident Test Bus", registration_number=f"BR01I{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="incident_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def test_hit_run_auto_spawns_incident_and_human_review_flow():
    bus_id, trip_id = setup_bus_and_trip()

    # Ingest a hit_run event
    hit_run_payload = {
        "event_type": "hit_run",
        "trip_id": str(trip_id),
        "bus_id": str(bus_id),
        "object_id": f"hit_{uuid.uuid4().hex[:6]}",
        "confidence": 0.94,
        "lon": 85.1400,
        "lat": 25.6000,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "severity": "high",
        "plate_text": "BR01AB1234",
        "plate_confidence": 0.96,
        "evidence_url": "/static/evidence/sample_hit_run.jpg",
    }

    resp = client.post("/api/v1/events", json=hit_run_payload, headers=AUTH_HEADERS)
    assert resp.status_code == 201
    event_id = resp.json()["id"]

    # 1. Verify incident was auto-spawned with status 'open'
    inc_resp = client.get("/api/v1/incidents?status=open")
    assert inc_resp.status_code == 200
    incidents = inc_resp.json()["items"]
    matching = [inc for inc in incidents if inc["primary_event_id"] == event_id]
    assert len(matching) == 1
    incident = matching[0]
    assert incident["status"] == "open"
    assert incident["suspected_plate"] == "BR01AB1234"

    # 2. Get Incident Detail (includes evidence items)
    incident_id = incident["id"]
    detail_resp = client.get(f"/api/v1/incidents/{incident_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == incident_id
    assert len(detail["evidence_items"]) >= 1

    # 3. Human Review Transition via PATCH /api/v1/incidents/{id}
    patch_payload = {
        "status": "under_review",
        "notes": "Officer assigned. Reviewing dashcam footage for BR01AB1234.",
    }
    patch_resp = client.patch(f"/api/v1/incidents/{incident_id}", json=patch_payload,headers=AUTH_HEADERS)
    assert patch_resp.status_code == 200
    updated = patch_resp.json()
    assert updated["status"] == "under_review"
    assert "Officer assigned" in updated["notes"]
