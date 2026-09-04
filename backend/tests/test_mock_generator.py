import uuid
from pydantic import TypeAdapter
from app.schemas.event import EventCreate
from scripts.mock_generator import GPSRouteSimulator, EventFactory, EVENT_TYPES

adapter = TypeAdapter(EventCreate)


def test_gps_route_simulator_advances():
    sim = GPSRouteSimulator(speed_kmh=30.0)
    p1 = sim.get_next_coordinate()
    assert len(p1) == 2
    assert -180 <= p1[0] <= 180  # lon
    assert -90 <= p1[1] <= 90   # lat


def test_all_event_types_pass_pydantic_validation():
    bus_id = uuid.uuid4()
    trip_id = uuid.uuid4()
    factory = EventFactory(bus_id=bus_id, trip_id=trip_id)

    for ev_type in EVENT_TYPES:
        ev_data = factory.build_event(ev_type, lon=85.1325, lat=25.5912)
        validated = adapter.validate_python(ev_data)
        assert validated.event_type == ev_type
        assert validated.bus_id == bus_id
        assert validated.trip_id == trip_id
        assert 0 <= validated.confidence <= 1


def test_burst_generator_shares_track_and_is_valid():
    bus_id = uuid.uuid4()
    trip_id = uuid.uuid4()
    factory = EventFactory(bus_id=bus_id, trip_id=trip_id)

    burst = factory.build_burst("pothole", base_lon=85.1325, base_lat=25.5912, frames=4)
    assert len(burst) == 4

    track_id = burst[0]["object_id"]
    for ev_data in burst:
        assert ev_data["object_id"] == track_id
        assert ev_data["event_type"] == "pothole"
        validated = adapter.validate_python(ev_data)
        assert validated.event_type == "pothole"
