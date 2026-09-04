import uuid
from datetime import datetime, timezone
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point
from app.db.session import SessionLocal
from app.models import Bus, Trip, Event

db = SessionLocal()

bus = Bus(name="Test Bus 1")
db.add(bus)
db.flush()

trip = Trip(bus_id=bus.id, started_at=datetime.now(timezone.utc), source="test")
db.add(trip)
db.flush()

point = from_shape(Point(85.13, 25.59), srid=4326)  # lon, lat — PostGIS order!

event = Event(
    event_type="pothole",
    trip_id=trip.id,
    bus_id=bus.id,
    confidence=0.93,
    location=point,
    occurred_at=datetime.now(timezone.utc),
)
db.add(event)
db.commit()

fetched = db.query(Event).filter(Event.id == event.id).first()
shape = to_shape(fetched.location)
print(f"Inserted and retrieved: lon={shape.x}, lat={shape.y}")

db.close()
