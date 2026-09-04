from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.repositories.analytics_repository import (
    get_defect_counts,
    get_heatmap_events,
    get_traffic_metrics,
)
from app.schemas.analytics import (
    HeatmapPoint,
    HeatmapResponse,
    RoadHealthSummaryResponse,
    TrafficAnalyticsResponse,
)

SEVERITY_WEIGHTS = {
    "high": 1.0,
    "medium": 0.65,
    "low": 0.35,
}


def generate_heatmap(
    db: Session,
    min_lon: Optional[float] = None,
    min_lat: Optional[float] = None,
    max_lon: Optional[float] = None,
    max_lat: Optional[float] = None,
    event_type: Optional[str] = None,
    limit: int = 1000,
) -> HeatmapResponse:
    events = get_heatmap_events(
        db,
        min_lon=min_lon,
        min_lat=min_lat,
        max_lon=max_lon,
        max_lat=max_lat,
        event_type=event_type,
        limit=limit,
    )

    points = []
    for ev in events:
        if ev.location is None:
            continue
        try:
            pt = to_shape(ev.location)
            base_weight = SEVERITY_WEIGHTS.get(ev.severity, 0.5)
            confidence_factor = float(ev.confidence) if ev.confidence is not None else 0.8
            final_weight = round(min(1.0, max(0.1, base_weight * confidence_factor)), 2)

            points.append(
                HeatmapPoint(
                    lon=round(pt.x, 6),
                    lat=round(pt.y, 6),
                    weight=final_weight,
                    event_type=ev.event_type,
                    severity=ev.severity,
                )
            )
        except Exception:
            continue

    return HeatmapResponse(total=len(points), points=points)


def compute_traffic_analytics(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> TrafficAnalyticsResponse:
    metrics = get_traffic_metrics(db, start_time, end_time)
    total_events = metrics["total_events"]

    if total_events > 50:
        congestion_level = "severe"
    elif total_events > 15:
        congestion_level = "moderate"
    else:
        congestion_level = "low"

    return TrafficAnalyticsResponse(
        total_events=total_events,
        anpr_count=metrics["anpr_count"],
        traffic_count=metrics["traffic_count"],
        congestion_level=congestion_level,
        average_confidence=metrics["average_confidence"],
    )


def compute_road_health_summary(
    db: Session,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> RoadHealthSummaryResponse:
    counts = get_defect_counts(db, start_time, end_time)
    potholes = counts.get("pothole", 0)
    waterlogging = counts.get("waterlogging", 0)
    signboard = counts.get("signboard_damage", 0)
    zebra = counts.get("zebra_crossing_issue", 0)

    total_defects = potholes + waterlogging + signboard + zebra

    # Calculate Road Quality Index (100 = Perfect, 0 = Worst)
    deductions = (potholes * 2.5) + (waterlogging * 4.0) + (signboard * 1.5) + (zebra * 1.0)
    rqi = round(max(0.0, min(100.0, 100.0 - deductions)), 1)

    if rqi >= 80.0:
        risk_level = "low"
    elif rqi >= 50.0:
        risk_level = "medium"
    else:
        risk_level = "high"

    return RoadHealthSummaryResponse(
        total_defects=total_defects,
        potholes_count=potholes,
        waterlogging_count=waterlogging,
        signboard_damage_count=signboard,
        zebra_crossing_issue_count=zebra,
        road_quality_index=rqi,
        risk_level=risk_level,
    )
