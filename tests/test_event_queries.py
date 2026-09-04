import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Bus, Trip
from app.schemas.event import PotholeEvent

client = TestClient(app)
AUTH_HEADERS = {"X-Service-Token": settings.service_token}


def setup_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="Query Test Bus", registration_number=f"BR01Q{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="query_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def test_spatial_and_filtered_queries():
    bus_id, trip_id = setup_bus_and_trip()

    # Ingest a test pothole event via POST endpoint
    payload = {
        "event_type": "pothole",
        "trip_id": str(trip_id),
        "bus_id": str(bus_id),
        "object_id": f"trk_{uuid.uuid4().hex[:6]}",
        "confidence": 0.88,
        "lon": 85.1330,
        "lat": 25.5970,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "severity": "high",
    }
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 201
    event_data = resp.json()
    event_id = event_data["id"]

    # 1. GET /api/v1/events (Filtered & Paginated)
    r = client.get(f"/api/v1/events?event_type=pothole&bus_id={bus_id}")
    assert r.status_code == 200
    res = r.json()
    assert res["total"] >= 1
    assert any(item["id"] == event_id for item in res["items"])

    # 2. GET /api/v1/events/{id}
    r = client.get(f"/api/v1/events/{event_id}")
    assert r.status_code == 200
    assert r.json()["id"] == event_id
    assert r.json()["severity"] == "high"

    # 3. GET /api/v1/events/nearby
    r = client.get(f"/api/v1/events/nearby?lon=85.1330&lat=25.5970&radius_m=500")
    assert r.status_code == 200
    assert r.json()["total"] >= 1

    # 4. GET /api/v1/events/bbox
    r = client.get("/api/v1/events/bbox?min_lon=85.12&min_lat=25.58&max_lon=85.15&max_lat=25.61")
    assert r.status_code == 200
    geojson = r.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) >= 1

    # 5. GET /api/v1/events/geojson
    r = client.get(f"/api/v1/events/geojson?event_type=pothole&bus_id={bus_id}")
    assert r.status_code == 200
    geojson = r.json()
    assert geojson["type"] == "FeatureCollection"
    assert len(geojson["features"]) >= 1