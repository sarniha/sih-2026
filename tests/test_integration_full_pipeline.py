import uuid
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.db.session import SessionLocal
from app.models import Bus, Event, Trip

client = TestClient(app)
AUTH_HEADERS = {"X-Service-Token": settings.service_token}


def setup_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="Integration Test Bus", registration_number=f"BR01X{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="integration_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def test_fake_event_flows_through_api_to_db_to_query_api():
    bus_id, trip_id = setup_bus_and_trip()

    lon, lat = 85.1450, 25.6040
    occurred_at = datetime.now(timezone.utc)

    payload = {
        "event_type": "pothole",
        "trip_id": str(trip_id),
        "bus_id": str(bus_id),
        "object_id": f"trk_integration_{uuid.uuid4().hex[:6]}",
        "confidence": 0.91,
        "lon": lon,
        "lat": lat,
        "occurred_at": occurred_at.isoformat(),
        "severity": "high",
    }

    # 1. POST the event via the real HTTP endpoint (through auth + validation)
    post_resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert post_resp.status_code == 201
    event_id = post_resp.json()["id"]

    # 2. Confirm the row actually landed in the DB — bypassing the service
    #    layer entirely, querying the ORM directly, so this doesn't just
    #    prove the API *returned* success, it proves persistence happened.
    db = SessionLocal()
    try:
        row = db.query(Event).filter(Event.id == uuid.UUID(event_id)).first()
        assert row is not None
        assert row.event_type == "pothole"
        assert row.severity == "high"
        assert float(row.confidence) == 0.91
        assert row.bus_id == bus_id
        assert row.trip_id == trip_id
    finally:
        db.close()

    # 3. GET the event back through the detail endpoint and confirm it
    #    matches what was posted.
    detail_resp = client.get(f"/api/v1/events/{event_id}")
    assert detail_resp.status_code == 200
    detail = detail_resp.json()
    assert detail["id"] == event_id
    assert detail["event_type"] == "pothole"
    assert detail["severity"] == "high"

    # 4. Confirm the event surfaces correctly through the spatial/GeoJSON
    #    query path, proving the PostGIS round-trip (lon/lat -> Geography
    #    -> back out as GeoJSON coordinates) is intact end to end.
    bbox_resp = client.get(
        "/api/v1/events/bbox",
        params={
            "min_lon": lon - 0.01,
            "min_lat": lat - 0.01,
            "max_lon": lon + 0.01,
            "max_lat": lat + 0.01,
        },
    )
    assert bbox_resp.status_code == 200
    geojson = bbox_resp.json()
    assert geojson["type"] == "FeatureCollection"

    matching_features = [
        f for f in geojson["features"] if f["properties"]["id"] == event_id
    ]
    assert len(matching_features) == 1

    feature = matching_features[0]
    assert feature["geometry"]["type"] == "Point"
    returned_lon, returned_lat = feature["geometry"]["coordinates"]
    assert abs(returned_lon - lon) < 1e-4
    assert abs(returned_lat - lat) < 1e-4