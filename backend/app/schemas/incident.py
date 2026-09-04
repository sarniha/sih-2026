from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class IncidentEvidenceResponse(BaseModel):
    id: UUID
    incident_id: UUID
    evidence_type: str
    url: str
    captured_at: datetime
    model_config = ConfigDict(from_attributes=True)


class IncidentResponse(BaseModel):
    id: UUID
    primary_event_id: UUID
    incident_type: str
    status: str
    suspected_plate: Optional[str] = None
    suspected_plate_confidence: Optional[float] = None
    lon: Optional[float] = None
    lat: Optional[float] = None
    occurred_at: datetime
    created_at: datetime
    notes: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)


class IncidentDetailResponse(IncidentResponse):
    evidence_items: List[IncidentEvidenceResponse] = []


class IncidentUpdate(BaseModel):
    status: Optional[Literal["open", "under_review", "closed", "dismissed"]] = None
    notes: Optional[str] = None


class PaginatedIncidentResponse(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[IncidentResponse]
