from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_Within
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import box

from app.models.event import Event


def get_heatmap_events(
    db: Session,
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    event_type: Optional[str] = None,
    limit: int = 1000,
) -> List[Event]:
    """Retrieve event locations for heatmap generation."""
    from sqlalchemy import cast

    query = db.query(Event).filter(Event.location.isnot(None))

    if min_lon is not None and min_lat is not None and max_lon is not None and max_lat is not None:
        bbox_shape = from_shape(box(min_lon, min_lat, max_lon, max_lat), srid=4326)
        query = query.filter(ST_Within(cast(Event.location, Geometry), bbox_shape))

    if event_type:
        query = query.filter(Event.event_type == event_type)

    return query.order_by(Event.occurred_at.desc()).limit(limit).all()


def get_traffic_metrics(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Query counts of traffic and ANPR events."""
    query = db.query(Event.event_type, func.count(Event.id), func.avg(Event.confidence)).filter(
        Event.event_type.in_(["traffic", "anpr"])
    )

    if start_time:
        query = query.filter(Event.occurred_at >= start_time)
    if end_time:
        query = query.filter(Event.occurred_at <= end_time)

    rows = query.group_by(Event.event_type).all()

    anpr_count = 0
    traffic_count = 0
    total_conf = 0.0
    total_count = 0

    for event_type, count, avg_conf in rows:
        if event_type == "anpr":
            anpr_count = count
        elif event_type == "traffic":
            traffic_count = count
        total_count += count
        total_conf += (float(avg_conf or 0.0) * count)

    avg_confidence = round(total_conf / total_count, 3) if total_count > 0 else 0.0

    return {
        "total_events": total_count,
        "anpr_count": anpr_count,
        "traffic_count": traffic_count,
        "average_confidence": avg_confidence,
    }


def get_defect_counts(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> Dict[str, int]:
    """Query counts of road defect event types."""
    defect_types = ["pothole", "waterlogging", "signboard_damage", "zebra_crossing_issue"]
    query = db.query(Event.event_type, func.count(Event.id)).filter(
        Event.event_type.in_(defect_types)
    )

    if start_time:
        query = query.filter(Event.occurred_at >= start_time)
    if end_time:
        query = query.filter(Event.occurred_at <= end_time)

    rows = query.group_by(Event.event_type).all()
    counts = {t: 0 for t in defect_types}
    for event_type, count in rows:
        counts[event_type] = count

    return counts
