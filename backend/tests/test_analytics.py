import uuid
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.models import Bus, Trip

client = TestClient(app)


def setup_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="Analytics Test Bus", registration_number=f"BR01A{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="analytics_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def test_traffic_heatmap_and_road_health_analytics():
    bus_id, trip_id = setup_bus_and_trip()

    # Ingest a defect event
    pothole_payload = {
        "event_type": "pothole",
        "trip_id": str(trip_id),
        "bus_id": str(bus_id),
        "object_id": f"pot_{uuid.uuid4().hex[:6]}",
        "confidence": 0.90,
        "lon": 85.1350,
        "lat": 25.5950,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "severity": "high",
    }
    client.post("/api/v1/events", json=pothole_payload)

    # Ingest a traffic event
    traffic_payload = {
        "event_type": "traffic",
        "trip_id": str(trip_id),
        "bus_id": str(bus_id),
        "object_id": f"traf_{uuid.uuid4().hex[:6]}",
        "confidence": 0.85,
        "lon": 85.1350,
        "lat": 25.5950,
        "occurred_at": datetime.now(timezone.utc).isoformat(),
        "severity": "medium",
    }
    client.post("/api/v1/events", json=traffic_payload)

    # 1. GET /api/v1/traffic/heatmap
    r1 = client.get("/api/v1/traffic/heatmap")
    assert r1.status_code == 200
    res1 = r1.json()
    assert res1["total"] >= 1
    assert "points" in res1

    # 2. GET /api/v1/traffic/analytics
    r2 = client.get("/api/v1/traffic/analytics")
    assert r2.status_code == 200
    res2 = r2.json()
    assert res2["total_events"] >= 1
    assert res2["congestion_level"] in ("low", "moderate", "severe")

    # 3. GET /api/v1/analytics/road-health
    r3 = client.get("/api/v1/analytics/road-health")
    assert r3.status_code == 200
    res3 = r3.json()
    assert "road_quality_index" in res3
    assert 0 <= res3["road_quality_index"] <= 100
    assert res3["risk_level"] in ("low", "medium", "high")
