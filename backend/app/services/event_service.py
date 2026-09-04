from typing import Any, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from geoalchemy2.shape import from_shape, to_shape
from shapely.geometry import Point

from app.models.event import Event
from app.repositories.event_repository import (
    create_event,
    find_duplicate_event,
    update_event,
)
from app.schemas.event import (
    EventCreate,
    EventDetailResponse,
    EventResponse,
    GeoJSONFeatureCollection,
    PaginatedEventResponse,
)



def ingest_event(db: Session, payload: EventCreate) -> EventResponse:
    """
    Ingest a new event payload with service-layer spatial-temporal deduplication.
    
    If an existing event with the same event_type exists within +/- 5 seconds and 
    10 meters (or same object_id), the existing row is updated if the incoming confidence
    is higher; otherwise the insertion is discarded and the canonical event is returned.
    """
    data = payload.model_dump()
    lon = data.pop("lon", None)
    lat = data.pop("lat", None)

    location = None
    if lon is not None and lat is not None:
        location = from_shape(Point(lon, lat), srid=4326)

    # 1. Deduplication Check
    existing = find_duplicate_event(
        db=db,
        event_type=data["event_type"],
        occurred_at=data["occurred_at"],
        location=location,
        object_id=data.get("object_id"),
        window_seconds=5.0,
        distance_meters=10.0,
    )

    if existing:
        new_confidence = data["confidence"]
        existing_confidence = float(existing.confidence)

        # Merge/upgrade fields if incoming confidence is higher
        if new_confidence > existing_confidence:
            updates = {
                "confidence": new_confidence,
                "bbox": data.get("bbox") or existing.bbox,
                "severity": data.get("severity") or existing.severity,
                "plate_text": data.get("plate_text") or existing.plate_text,
                "plate_confidence": data.get("plate_confidence") or existing.plate_confidence,
                "evidence_url": data.get("evidence_url") or existing.evidence_url,
            }
            existing = update_event(db, existing, updates)

        existing_lon, existing_lat = lon, lat
        if existing.location is not None:
            try:
                pt = to_shape(existing.location)
                existing_lon = round(pt.x, 6)
                existing_lat = round(pt.y, 6)
            except Exception:
                pass

        return EventResponse(
            id=existing.id,
            event_type=existing.event_type,
            trip_id=existing.trip_id,
            bus_id=existing.bus_id,
            confidence=float(existing.confidence),
            lon=existing_lon,
            lat=existing_lat,
            occurred_at=existing.occurred_at,
            created_at=existing.created_at,
            severity=existing.severity,
            status=existing.status,
        )

    # 2. No Duplicate Found -> Create New Row
    event = Event(
        event_type=data["event_type"],
        trip_id=data["trip_id"],
        bus_id=data["bus_id"],
        camera_id=data.get("camera_id"),
        object_id=data.get("object_id"),
        confidence=data["confidence"],
        bbox=data.get("bbox"),
        location=location,
        occurred_at=data["occurred_at"],
        severity=data.get("severity"),
        plate_text=data.get("plate_text"),
        plate_confidence=data.get("plate_confidence"),
        evidence_url=data.get("evidence_url"),
    )

    saved = create_event(db, event)

    try:
        from app.services.incident_service import evaluate_and_spawn_incident
        evaluate_and_spawn_incident(db, saved)
    except Exception:
        pass

    response = _event_to_response(saved, fallback_lon=lon, fallback_lat=lat)

    try:
        import asyncio
        from app.services.websocket_manager import ws_manager
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.run_coroutine_threadsafe(ws_manager.broadcast_event(response.model_dump()), loop)
    except Exception:
        pass

    return response




def _extract_lon_lat(event: Event, fallback_lon: Optional[float] = None, fallback_lat: Optional[float] = None):
    if event.location is not None:
        try:
            pt = to_shape(event.location)
            return round(pt.x, 6), round(pt.y, 6)
        except Exception:
            pass
    return fallback_lon, fallback_lat


def _event_to_response(event: Event, fallback_lon: Optional[float] = None, fallback_lat: Optional[float] = None) -> EventResponse:
    lon, lat = _extract_lon_lat(event, fallback_lon, fallback_lat)
    return EventResponse(
        id=event.id,
        event_type=event.event_type,
        trip_id=event.trip_id,
        bus_id=event.bus_id,
        confidence=float(event.confidence) if event.confidence is not None else 0.0,
        lon=lon,
        lat=lat,
        occurred_at=event.occurred_at,
        created_at=event.created_at,
        severity=event.severity,
        status=event.status,
        camera_id=event.camera_id,
        object_id=event.object_id,
        plate_text=event.plate_text,
        plate_confidence=float(event.plate_confidence) if event.plate_confidence is not None else None,
        evidence_url=event.evidence_url,
    )


def _event_to_detail_response(event: Event) -> EventDetailResponse:
    lon, lat = _extract_lon_lat(event)
    return EventDetailResponse(
        id=event.id,
        event_type=event.event_type,
        trip_id=event.trip_id,
        bus_id=event.bus_id,
        confidence=float(event.confidence) if event.confidence is not None else 0.0,
        lon=lon,
        lat=lat,
        occurred_at=event.occurred_at,
        created_at=event.created_at,
        severity=event.severity,
        status=event.status,
        camera_id=event.camera_id,
        object_id=event.object_id,
        bbox=event.bbox,
        plate_text=event.plate_text,
        plate_confidence=float(event.plate_confidence) if event.plate_confidence is not None else None,
        evidence_url=event.evidence_url,
        metadata_=event.metadata_,
    )


def _event_to_geojson_feature(event: Event) -> Dict[str, Any]:
    lon, lat = _extract_lon_lat(event)
    coordinates = [lon if lon is not None else 0.0, lat if lat is not None else 0.0]
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": coordinates,
        },
        "properties": {
            "id": str(event.id),
            "event_type": event.event_type,
            "trip_id": str(event.trip_id),
            "bus_id": str(event.bus_id),
            "confidence": float(event.confidence) if event.confidence is not None else None,
            "severity": event.severity,
            "status": event.status,
            "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "evidence_url": event.evidence_url,
            "plate_text": event.plate_text,
        },
    }


def list_events(
    db: Session,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    trip_id: Optional[Any] = None,
    bus_id: Optional[Any] = None,
    start_time: Optional[Any] = None,
    end_time: Optional[Any] = None,
    limit: int = 100,
    offset: int = 0,
) -> PaginatedEventResponse:
    from app.repositories.event_repository import get_events
    total, items = get_events(
        db=db,
        event_type=event_type,
        severity=severity,
        status=status,
        trip_id=trip_id,
        bus_id=bus_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    return PaginatedEventResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_event_to_response(item) for item in items],
    )


def get_event_detail(db: Session, event_id: Any) -> Optional[EventDetailResponse]:
    from app.repositories.event_repository import get_event_by_id
    event = get_event_by_id(db, event_id)
    if not event:
        return None
    return _event_to_detail_response(event)


def get_nearby_events(
    db: Session,
    lon: float,
    lat: float,
    radius_m: float = 500.0,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> PaginatedEventResponse:
    from app.repositories.event_repository import get_events_nearby
    total, items = get_events_nearby(
        db=db,
        lon=lon,
        lat=lat,
        radius_m=radius_m,
        event_type=event_type,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return PaginatedEventResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_event_to_response(item) for item in items],
    )


def get_bbox_geojson(
    db: Session,
    min_lon: float,
    min_lat: float,
    max_lon: float,
    max_lat: float,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 500,
    offset: int = 0,
) -> GeoJSONFeatureCollection:
    from app.repositories.event_repository import get_events_bbox
    _, items = get_events_bbox(
        db=db,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        event_type=event_type,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    features = [_event_to_geojson_feature(item) for item in items]
    return GeoJSONFeatureCollection(features=features)


def get_filtered_geojson(
    db: Session,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    trip_id: Optional[Any] = None,
    bus_id: Optional[Any] = None,
    limit: int = 500,
    offset: int = 0,
) -> GeoJSONFeatureCollection:
    from app.repositories.event_repository import get_events
    _, items = get_events(
        db=db,
        event_type=event_type,
        severity=severity,
        status=status,
        trip_id=trip_id,
        bus_id=bus_id,
        limit=limit,
        offset=offset,
    )
    features = [_event_to_geojson_feature(item) for item in items]
    return GeoJSONFeatureCollection(features=features)