from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import verify_service_token

from app.db.session import get_db
from app.schemas.event import (
    EventCreate,
    EventDetailResponse,
    EventResponse,
    GeoJSONFeatureCollection,
    PaginatedEventResponse,
)
from app.services.event_service import (
    get_bbox_geojson,
    get_event_detail,
    get_filtered_geojson,
    get_nearby_events,
    ingest_event,
    list_events,
)

router = APIRouter()


@router.post("/events", response_model=EventResponse, status_code=201,dependencies=[Depends(verify_service_token)])
def create_event_endpoint(payload: EventCreate, db: Session = Depends(get_db)):
    return ingest_event(db, payload)


@router.get("/events", response_model=PaginatedEventResponse)
def get_events_endpoint(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    trip_id: Optional[UUID] = Query(None),
    bus_id: Optional[UUID] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_events(
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


@router.get("/events/nearby", response_model=PaginatedEventResponse)
def get_events_nearby_endpoint(
    lon: float = Query(...),
    lat: float = Query(...),
    radius_m: float = Query(500.0, gt=0),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return get_nearby_events(
        db=db,
        lon=lon,
        lat=lat,
        radius_m=radius_m,
        event_type=event_type,
        severity=severity,
        limit=limit,
        offset=offset,
    )


@router.get("/events/bbox", response_model=GeoJSONFeatureCollection)
def get_events_bbox_endpoint(
    min_lon: float = Query(...),
    min_lat: float = Query(...),
    max_lon: float = Query(...),
    max_lat: float = Query(...),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return get_bbox_geojson(
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


@router.get("/events/geojson", response_model=GeoJSONFeatureCollection)
def get_events_geojson_endpoint(
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    trip_id: Optional[UUID] = Query(None),
    bus_id: Optional[UUID] = Query(None),
    limit: int = Query(500, ge=1, le=2000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return get_filtered_geojson(
        db=db,
        event_type=event_type,
        severity=severity,
        status=status,
        trip_id=trip_id,
        bus_id=bus_id,
        limit=limit,
        offset=offset,
    )


@router.get("/events/{event_id}", response_model=EventDetailResponse)
def get_event_detail_endpoint(event_id: UUID, db: Session = Depends(get_db)):
    detail = get_event_detail(db, event_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Event not found")
    return detail
