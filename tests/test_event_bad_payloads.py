from app.core.config import settings
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

AUTH_HEADERS = {"X-Service-Token": settings.service_token}

VALID_POTHOLE = {
    "event_type": "pothole",
    "trip_id": "00000000-0000-0000-0000-000000000000",
    "bus_id": "00000000-0000-0000-0000-000000000000",
    "confidence": 0.85,
    "lon": 85.1330,
    "lat": 25.5970,
    "occurred_at": "2026-01-01T00:00:00Z",
    "severity": "low",
}


def test_missing_occurred_at_returns_422():
    payload = {k: v for k, v in VALID_POTHOLE.items() if k != "occurred_at"}
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422
    detail = resp.json()["detail"]
    assert any(
        "occurred_at" in err["loc"] and err["type"] == "missing" for err in detail
    )


def test_invalid_event_type_returns_422():
    payload = {**VALID_POTHOLE, "event_type": "not_a_real_type"}
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422


def test_confidence_over_one_returns_422():
    payload = {**VALID_POTHOLE, "confidence": 1.5}
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422


def test_confidence_below_zero_returns_422():
    payload = {**VALID_POTHOLE, "confidence": -0.1}
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422


def test_anpr_without_plate_text_returns_422_via_api():
    # Mirrors test_event_schemas.py's schema-level check, but through the
    # actual HTTP endpoint + auth dependency chain, not just the Pydantic
    # model in isolation.
    payload = {
        "event_type": "anpr",
        "trip_id": "00000000-0000-0000-0000-000000000000",
        "bus_id": "00000000-0000-0000-0000-000000000000",
        "confidence": 0.9,
        "lon": 85.1330,
        "lat": 25.5970,
        "occurred_at": "2026-01-01T00:00:00Z",
        # plate_text and plate_confidence deliberately omitted
    }
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422


def test_malformed_json_body_returns_422():
    resp = client.post(
        "/api/v1/events",
        data="{not valid json",
        headers={**AUTH_HEADERS, "Content-Type": "application/json"},
    )
    assert resp.status_code == 422


def test_invalid_severity_value_returns_422():
    payload = {**VALID_POTHOLE, "severity": "catastrophic"}
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422


def test_lon_out_of_range_returns_422():
    payload = {**VALID_POTHOLE, "lon": 999.0}
    resp = client.post("/api/v1/events", json=payload, headers=AUTH_HEADERS)
    assert resp.status_code == 422