from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_fleet_summary_and_system_health():
    # 1. GET /api/v1/fleet/summary
    r1 = client.get("/api/v1/fleet/summary")
    assert r1.status_code == 200
    fleet = r1.json()
    assert "total_buses" in fleet
    assert "active_buses" in fleet
    assert "buses" in fleet

    # 2. GET /api/v1/fleet/cameras
    r2 = client.get("/api/v1/fleet/cameras")
    assert r2.status_code == 200
    assert "cameras" in r2.json()

    # 3. GET /api/v1/health/system
    r3 = client.get("/api/v1/health/system")
    assert r3.status_code == 200
    health = r3.json()
    assert health["status"] in ("ok", "degraded")
    assert health["database"] == "connected"
    assert "total_events" in health
    assert "total_incidents" in health
    assert "evidence_storage_bytes" in health
