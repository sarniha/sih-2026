from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session
from geoalchemy2.functions import ST_DWithin
from geoalchemy2.shape import from_shape
from shapely.geometry import Point, box


from app.models.event import Event


def create_event(db: Session, event: Event) -> Event:
    """Insert a new event into the database."""
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def find_duplicate_event(
    db: Session,
    event_type: str,
    occurred_at: datetime,
    location: Optional[Any] = None,
    object_id: Optional[str] = None,
    window_seconds: float = 5.0,
    distance_meters: float = 10.0,
) -> Optional[Event]:
    """
    Query existing events matching event_type within a time window (+/- window_seconds)
    and spatial distance (distance_meters in PostGIS ST_DWithin).
    Matches by object_id or spatial proximity.
    """
    time_min = occurred_at - timedelta(seconds=window_seconds)
    time_max = occurred_at + timedelta(seconds=window_seconds)

    query = db.query(Event).filter(
        Event.event_type == event_type,
        Event.occurred_at >= time_min,
        Event.occurred_at <= time_max,
    )

    spatial_cond = None
    if location is not None:
        spatial_cond = ST_DWithin(Event.location, location, distance_meters)

    object_cond = None
    if object_id:
        object_cond = (Event.object_id == object_id)

    if spatial_cond is not None and object_cond is not None:
        query = query.filter(or_(object_cond, spatial_cond))
    elif spatial_cond is not None:
        query = query.filter(spatial_cond)
    elif object_cond is not None:
        query = query.filter(object_cond)

    return query.order_by(Event.occurred_at.desc()).first()


def update_event(db: Session, event: Event, updates: Dict[str, Any]) -> Event:
    """Update attributes on an existing Event row and commit."""
    for key, value in updates.items():
        if value is not None:
            setattr(event, key, value)
    db.commit()
    db.refresh(event)
    return event


def get_event_by_id(db: Session, event_id: Any) -> Optional[Event]:
    """Retrieve single event by primary key UUID."""
    return db.query(Event).filter(Event.id == event_id).first()


def get_events(
    db: Session,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    trip_id: Optional[Any] = None,
    bus_id: Optional[Any] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Filtered & paginated query for events."""
    query = db.query(Event)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    if severity:
        query = query.filter(Event.severity == severity)
    if status:
        query = query.filter(Event.status == status)
    if trip_id:
        query = query.filter(Event.trip_id == trip_id)
    if bus_id:
        query = query.filter(Event.bus_id == bus_id)
    if start_time:
        query = query.filter(Event.occurred_at >= start_time)
    if end_time:
        query = query.filter(Event.occurred_at <= end_time)

    total = query.count()
    items = query.order_by(Event.occurred_at.desc()).offset(offset).limit(limit).all()
    return total, items


def get_events_nearby(
    db: Session,
    lon: float,
    lat: float,
    radius_m: float = 500.0,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Spatial radius query using PostGIS ST_DWithin."""
    center = from_shape(Point(lon, lat), srid=4326)
    query = db.query(Event).filter(ST_DWithin(Event.location, center, radius_m))

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if severity:
        query = query.filter(Event.severity == severity)

    total = query.count()
    items = query.order_by(Event.occurred_at.desc()).offset(offset).limit(limit).all()
    return total, items


def get_events_bbox(
    db: Session,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
):
    """Bounding box spatial query using Shapely box & GeoAlchemy2 ST_Within."""
    from sqlalchemy import cast
    from geoalchemy2 import Geometry
    from geoalchemy2.functions import ST_Within

    bbox_shape = from_shape(box(min_lon, min_lat, max_lon, max_lat), srid=4326)
    query = db.query(Event).filter(ST_Within(cast(Event.location, Geometry), bbox_shape))

    if event_type:
        query = query.filter(Event.event_type == event_type)
    if severity:
        query = query.filter(Event.severity == severity)

    total = query.count()
    items = query.order_by(Event.occurred_at.desc()).offset(offset).limit(limit).all()
    return total, items