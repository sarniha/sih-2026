import os
from datetime import datetime, timezone
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.models.bus import Bus
from app.models.camera import Camera
from app.models.event import Event
from app.models.incident import Incident
from app.models.trip import Trip
from app.schemas.fleet import (
    BusStatusResponse,
    CameraStatusResponse,
    FleetSummaryResponse,
    SystemHealthResponse,
)
from app.services.evidence_service import EVIDENCE_DIR
from app.services.websocket_manager import ws_manager


def get_fleet_summary(db: Session) -> FleetSummaryResponse:
    buses = db.query(Bus).all()
    cameras = db.query(Camera).all()

    bus_responses = []
    active_buses_count = 0
    for bus in buses:
        trip_count = db.query(func.count(Trip.id)).filter(Trip.bus_id == bus.id).scalar() or 0
        last_trip = db.query(Trip).filter(Trip.bus_id == bus.id).order_by(Trip.started_at.desc()).first()
        is_active = trip_count > 0

        if is_active:
            active_buses_count += 1

        bus_responses.append(
            BusStatusResponse(
                id=bus.id,
                name=bus.name,
                registration_number=bus.registration_number,
                is_active=is_active,
                total_trips=trip_count,
                last_trip_started_at=last_trip.started_at if last_trip else None,
            )
        )

    camera_responses = []
    online_cameras_count = 0
    for cam in cameras:
        status = "online"  # Demo edge camera state
        online_cameras_count += 1
        camera_responses.append(
            CameraStatusResponse(
                id=cam.id,
                bus_id=cam.bus_id,
                name=cam.name,
                camera_type=cam.camera_type,
                status=status,
                last_heartbeat=datetime.now(timezone.utc),
            )
        )

    return FleetSummaryResponse(
        total_buses=len(buses),
        active_buses=active_buses_count,
        total_cameras=len(cameras),
        online_cameras=online_cameras_count,
        buses=bus_responses,
        cameras=camera_responses,
    )


def get_system_diagnostics(db: Session) -> SystemHealthResponse:
    # 1. DB Connectivity Check & Row Counts
    db_status = "connected"
    total_events = 0
    total_incidents = 0
    try:
        db.execute(text("SELECT 1"))
        total_events = db.query(func.count(Event.id)).scalar() or 0
        total_incidents = db.query(func.count(Incident.id)).scalar() or 0
    except Exception as e:
        db_status = f"error: {str(e)}"

    # 2. WebSocket Connections
    ws_connections = ws_manager.get_total_active_connections()

    # 3. Evidence Storage Inspection
    storage_files = 0
    storage_bytes = 0
    if os.path.exists(EVIDENCE_DIR):
        for entry in os.scandir(EVIDENCE_DIR):
            if entry.is_file():
                storage_files += 1
                storage_bytes += entry.stat().st_size

    system_status = "ok" if db_status == "connected" else "degraded"

    return SystemHealthResponse(
        status=system_status,
        database=db_status,
        total_events=total_events,
        total_incidents=total_incidents,
        active_ws_connections=ws_connections,
        evidence_storage_files=storage_files,
        evidence_storage_bytes=storage_bytes,
        server_time=datetime.now(timezone.utc),
    )
