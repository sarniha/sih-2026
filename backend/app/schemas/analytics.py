from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class HeatmapPoint(BaseModel):
    lon: float
    lat: float
    weight: float = Field(ge=0, le=1)
    event_type: str
    severity: Optional[str] = None


class HeatmapResponse(BaseModel):
    total: int
    points: List[HeatmapPoint]


class TrafficAnalyticsResponse(BaseModel):
    total_events: int
    anpr_count: int
    traffic_count: int
    congestion_level: Literal["low", "moderate", "severe"]
    average_confidence: float


class RoadHealthSummaryResponse(BaseModel):
    total_defects: int
    potholes_count: int
    waterlogging_count: int
    signboard_damage_count: int
    zebra_crossing_issue_count: int
    road_quality_index: float  # 0 to 100 scale (100 = perfect road, 0 = severe damage)
    risk_level: Literal["low", "medium", "high"]
