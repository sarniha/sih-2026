from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    HeatmapResponse,
    RoadHealthSummaryResponse,
    TrafficAnalyticsResponse,
)
from app.services.analytics_service import (
    compute_road_health_summary,
    compute_traffic_analytics,
    generate_heatmap,
)

router = APIRouter()


@router.get("/traffic/heatmap", response_model=HeatmapResponse)
def get_traffic_heatmap_endpoint(
    min_lon: Optional[float] = Query(None),
    min_lat: Optional[float] = Query(None),
    max_lon: Optional[float] = Query(None),
    max_lat: Optional[float] = Query(None),
    event_type: Optional[str] = Query(None),
    limit: int = Query(1000, ge=1, le=5000),
    db: Session = Depends(get_db),
):
    return generate_heatmap(
        db,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        event_type=event_type,
        limit=limit,
    )


@router.get("/traffic/analytics", response_model=TrafficAnalyticsResponse)
def get_traffic_analytics_endpoint(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    return compute_traffic_analytics(db, start_time=start_time, end_time=end_time)


@router.get("/analytics/road-health", response_model=RoadHealthSummaryResponse)
def get_road_health_summary_endpoint(
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    db: Session = Depends(get_db),
):
    return compute_road_health_summary(db, start_time=start_time, end_time=end_time)
