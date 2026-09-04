from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class BusStatusResponse(BaseModel):
    id: UUID
    name: Optional[str] = "Unassigned Bus"
    registration_number: Optional[str] = "N/A"
    is_active: bool
    total_trips: int
    last_trip_started_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)



class CameraStatusResponse(BaseModel):
    id: UUID
    bus_id: UUID
    name: str
    camera_type: str
    status: Literal["online", "offline"]
    last_heartbeat: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


class FleetSummaryResponse(BaseModel):
    total_buses: int
    active_buses: int
    total_cameras: int
    online_cameras: int
    buses: List[BusStatusResponse]
    cameras: List[CameraStatusResponse]


class SystemHealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    database: str
    total_events: int
    total_incidents: int
    active_ws_connections: int
    evidence_storage_files: int
    evidence_storage_bytes: int
    server_time: datetime
