from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventBase(BaseModel):
    trip_id: UUID
    bus_id: UUID
    camera_id: Optional[UUID] = None
    object_id: Optional[str] = None
    confidence: float = Field(ge=0, le=1)
    bbox: Optional[dict] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    occurred_at: datetime
    severity: Optional[Literal["low", "medium", "high"]] = None
    evidence_url: Optional[str] = None

    @field_validator("lon")
    @classmethod
    def lon_range(cls, v):
        if v is not None and not (-180 <= v <= 180):
            raise ValueError("lon must be between -180 and 180")
        return v

    @field_validator("lat")
    @classmethod
    def lat_range(cls, v):
        if v is not None and not (-90 <= v <= 90):
            raise ValueError("lat must be between -90 and 90")
        return v


class PotholeEvent(EventBase):
    event_type: Literal["pothole"]


class WaterloggingEvent(EventBase):
    event_type: Literal["waterlogging"]


class SignboardDamageEvent(EventBase):
    event_type: Literal["signboard_damage"]


class ZebraCrossingIssueEvent(EventBase):
    event_type: Literal["zebra_crossing_issue"]


class TrafficEvent(EventBase):
    event_type: Literal["traffic"]


class AnprEvent(EventBase):
    event_type: Literal["anpr"]
    plate_text: str
    plate_confidence: float = Field(ge=0, le=1)


class HitRunEvent(EventBase):
    event_type: Literal["hit_run"]
    plate_text: Optional[str] = None
    plate_confidence: Optional[float] = Field(default=None, ge=0, le=1)


EventCreate = Union[
    PotholeEvent,
    WaterloggingEvent,
    SignboardDamageEvent,
    ZebraCrossingIssueEvent,
    TrafficEvent,
    AnprEvent,
    HitRunEvent,
]


class EventResponse(BaseModel):
    id: UUID
    event_type: str
    trip_id: UUID
    bus_id: UUID
    confidence: float
    lon: Optional[float] = None
    lat: Optional[float] = None
    occurred_at: datetime
    created_at: datetime
    severity: Optional[str] = None
    status: str
    model_config = ConfigDict(from_attributes=True)


class EventDetailResponse(EventResponse):
    camera_id: Optional[UUID] = None
    object_id: Optional[str] = None
    bbox: Optional[dict] = None
    plate_text: Optional[str] = None
    plate_confidence: Optional[float] = None
    evidence_url: Optional[str] = None
    metadata_: Optional[dict] = None


class PaginatedEventResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[EventResponse]


# GeoJSON schemas matching RFC 7946 for Leaflet map integration
class GeoJSONFeatureGeometry(BaseModel):
    type: Literal["Point"] = "Point"
    coordinates: List[float]  # [longitude, latitude]


class GeoJSONFeature(BaseModel):
    type: Literal["Feature"] = "Feature"
    geometry: GeoJSONFeatureGeometry
    properties: Dict[str, Any]


class GeoJSONFeatureCollection(BaseModel):
    type: Literal["FeatureCollection"] = "FeatureCollection"
    features: List[GeoJSONFeature]