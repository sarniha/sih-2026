import uuid
from datetime import datetime, timezone, timedelta
from app.db.session import SessionLocal
from app.models import Bus, Trip, Event
from app.schemas.event import PotholeEvent, WaterloggingEvent
from app.services.event_service import ingest_event


def setup_demo_bus_and_trip():
    db = SessionLocal()
    bus = Bus(name="Dedup Test Bus", registration_number=f"BR01D{uuid.uuid4().hex[:4]}")
    db.add(bus)
    db.flush()

    trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="dedup_test")
    db.add(trip)
    db.commit()
    db.refresh(bus)
    db.refresh(trip)
    db.close()
    return bus.id, trip.id


def test_burst_deduplication_collapses_to_single_row():
    bus_id, trip_id = setup_demo_bus_and_trip()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        object_id = f"trk_pothole_{uuid.uuid4().hex[:6]}"
        
        responses = []
        for i in range(10):
            payload = PotholeEvent(
                event_type="pothole",
                trip_id=trip_id,
                bus_id=bus_id,
                object_id=object_id,
                confidence=0.80 + (i * 0.01),
                lon=85.13250 + (i * 0.000005),  # ~0.5m jitter
                lat=25.59120 + (i * 0.000005),
                occurred_at=now + timedelta(milliseconds=i * 150),
                severity="medium",
            )
            resp = ingest_event(db, payload)
            responses.append(resp)

        # Assert all 10 ingest calls return the exact same canonical Event ID
        first_id = responses[0].id
        for r in responses:
            assert r.id == first_id

        # Assert only 1 row exists in DB for this object_id
        db_rows = db.query(Event).filter(Event.object_id == object_id).all()
        assert len(db_rows) == 1
        # Assert highest confidence was updated (0.80 + 9*0.01 = 0.89)
        assert float(db_rows[0].confidence) == 0.89
    finally:
        db.close()


def test_higher_confidence_updates_existing_event():
    bus_id, trip_id = setup_demo_bus_and_trip()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        obj_id = f"trk_conf_{uuid.uuid4().hex[:6]}"

        p1 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            object_id=obj_id,
            confidence=0.72,
            lon=85.1330,
            lat=25.5920,
            occurred_at=now,
            severity="low",
        )
        r1 = ingest_event(db, p1)

        p2 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            object_id=obj_id,
            confidence=0.95,
            lon=85.1330,
            lat=25.5920,
            occurred_at=now + timedelta(seconds=1),
            severity="high",
        )
        r2 = ingest_event(db, p2)

        assert r1.id == r2.id
        row = db.query(Event).filter(Event.id == r1.id).first()
        assert float(row.confidence) == 0.95
        assert row.severity == "high"
    finally:
        db.close()


def test_lower_confidence_does_not_downgrade():
    bus_id, trip_id = setup_demo_bus_and_trip()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        obj_id = f"trk_nodown_{uuid.uuid4().hex[:6]}"

        p1 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            object_id=obj_id,
            confidence=0.90,
            lon=85.1340,
            lat=25.5930,
            occurred_at=now,
            severity="high",
        )
        r1 = ingest_event(db, p1)

        p2 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            object_id=obj_id,
            confidence=0.65,
            lon=85.1340,
            lat=25.5930,
            occurred_at=now + timedelta(seconds=1),
            severity="low",
        )
        r2 = ingest_event(db, p2)

        assert r1.id == r2.id
        row = db.query(Event).filter(Event.id == r1.id).first()
        assert float(row.confidence) == 0.90
        assert row.severity == "high"
    finally:
        db.close()


def test_time_window_boundary_creates_new_row():
    bus_id, trip_id = setup_demo_bus_and_trip()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        obj_id = f"trk_time_{uuid.uuid4().hex[:6]}"

        p1 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            object_id=obj_id,
            confidence=0.85,
            lon=85.1350,
            lat=25.5940,
            occurred_at=now,
        )
        r1 = ingest_event(db, p1)

        # 10 seconds later (> 5s window)
        p2 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            object_id=obj_id,
            confidence=0.85,
            lon=85.1350,
            lat=25.5940,
            occurred_at=now + timedelta(seconds=10),
        )
        r2 = ingest_event(db, p2)

        assert r1.id != r2.id
    finally:
        db.close()


def test_distance_boundary_creates_new_row():
    bus_id, trip_id = setup_demo_bus_and_trip()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        p1 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            confidence=0.85,
            lon=85.1300,
            lat=25.5900,
            occurred_at=now,
        )
        r1 = ingest_event(db, p1)

        # ~2.5 km away (> 10m distance)
        p2 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            confidence=0.85,
            lon=85.1500,
            lat=25.6100,
            occurred_at=now + timedelta(seconds=1),
        )
        r2 = ingest_event(db, p2)

        assert r1.id != r2.id
    finally:
        db.close()


def test_different_event_types_create_new_rows():
    bus_id, trip_id = setup_demo_bus_and_trip()
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        p1 = PotholeEvent(
            event_type="pothole",
            trip_id=trip_id,
            bus_id=bus_id,
            confidence=0.85,
            lon=85.1360,
            lat=25.5950,
            occurred_at=now,
        )
        r1 = ingest_event(db, p1)

        p2 = WaterloggingEvent(
            event_type="waterlogging",
            trip_id=trip_id,
            bus_id=bus_id,
            confidence=0.85,
            lon=85.1360,
            lat=25.5950,
            occurred_at=now,
        )
        r2 = ingest_event(db, p2)

        assert r1.id != r2.id
    finally:
        db.close()
