import pytest
from pydantic import TypeAdapter, ValidationError
from app.schemas.event import EventCreate

adapter = TypeAdapter(EventCreate)


def test_valid_pothole_passes():
    payload = {
        "event_type": "pothole",
        "trip_id": "00000000-0000-0000-0000-000000000001",
        "bus_id": "00000000-0000-0000-0000-000000000002",
        "confidence": 0.85,
        "occurred_at": "2026-09-04T10:00:00Z",
    }
    result = adapter.validate_python(payload)
    assert result.event_type == "pothole"


def test_anpr_without_plate_text_fails():
    payload = {
        "event_type": "anpr",
        "trip_id": "00000000-0000-0000-0000-000000000001",
        "bus_id": "00000000-0000-0000-0000-000000000002",
        "confidence": 0.85,
        "occurred_at": "2026-09-04T10:00:00Z",
        # plate_text deliberately missing
    }
    with pytest.raises(ValidationError):
        adapter.validate_python(payload)


def test_confidence_over_one_fails():
    payload = {
        "event_type": "pothole",
        "trip_id": "00000000-0000-0000-0000-000000000001",
        "bus_id": "00000000-0000-0000-0000-000000000002",
        "confidence": 1.5,
        "occurred_at": "2026-09-04T10:00:00Z",
    }
    with pytest.raises(ValidationError):
        adapter.validate_python(payload)


def test_pothole_with_metadata_passes():
    payload = {
        "event_type": "pothole",
        "trip_id": "00000000-0000-0000-0000-000000000001",
        "bus_id": "00000000-0000-0000-0000-000000000002",
        "confidence": 0.85,
        "occurred_at": "2026-09-04T10:00:00Z",
        "metadata": {"defect_class": "alligator_crack", "severity_score": 85},
    }
    result = adapter.validate_python(payload)
    assert result.event_type == "pothole"
    assert result.metadata["defect_class"] == "alligator_crack"