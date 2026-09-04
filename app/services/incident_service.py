from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from geoalchemy2.shape import to_shape

from app.models.event import Event
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence
from app.repositories.incident_repository import (
    create_incident,
    create_incident_evidence,
    get_incident_by_id,
    get_incidents,
    update_incident,
)
from app.schemas.incident import (
    IncidentDetailResponse,
    IncidentEvidenceResponse,
    IncidentResponse,
    IncidentUpdate,
    PaginatedIncidentResponse,
)
from app.services.evidence_service import generate_sample_evidence


def _extract_lon_lat(incident: Incident) -> Tuple[Optional[float], Optional[float]]:
    if incident.location is not None:
        try:
            pt = to_shape(incident.location)
            return round(pt.x, 6), round(pt.y, 6)
        except Exception:
            pass
    return None, None


def _incident_to_response(incident: Incident) -> IncidentResponse:
    lon, lat = _extract_lon_lat(incident)
    return IncidentResponse(
        id=incident.id,
        primary_event_id=incident.primary_event_id,
        incident_type=incident.incident_type,
        status=incident.status,
        suspected_plate=incident.suspected_plate,
        suspected_plate_confidence=float(incident.suspected_plate_confidence) if incident.suspected_plate_confidence is not None else None,
        lon=lon,
        lat=lat,
        occurred_at=incident.occurred_at,
        created_at=incident.created_at,
        notes=incident.notes,
    )


def _incident_to_detail_response(incident: Incident) -> IncidentDetailResponse:
    resp = _incident_to_response(incident)
    evidence_items = [
        IncidentEvidenceResponse(
            id=item.id,
            incident_id=item.incident_id,
            evidence_type=item.evidence_type,
            url=item.url,
            captured_at=item.captured_at,
        )
        for item in (incident.evidence_items or [])
    ]
    return IncidentDetailResponse(
        **resp.model_dump(),
        evidence_items=evidence_items,
    )


def evaluate_and_spawn_incident(db: Session, event: Event) -> Optional[Incident]:
    """
    Automated incident spawning logic when a safety-critical event (like hit_run) is ingested.
    """
    if event.event_type not in ("hit_run", "suspected_collision"):
        return None

    incident_type = "suspected_hit_and_run" if event.event_type == "hit_run" else "suspected_collision"

    incident = Incident(
        primary_event_id=event.id,
        incident_type=incident_type,
        status="open",
        suspected_plate=event.plate_text,
        suspected_plate_confidence=event.plate_confidence,
        location=event.location,
        occurred_at=event.occurred_at,
        notes=f"Auto-spawned from AI detection pipeline ({event.event_type}).",
    )
    saved_incident = create_incident(db, incident)

    # Attach evidence items
    if event.evidence_url:
        create_incident_evidence(
            db,
            IncidentEvidence(
                incident_id=saved_incident.id,
                evidence_type="image",
                url=event.evidence_url,
                captured_at=event.occurred_at,
            ),
        )
    else:
        # Generate sample filesystem evidence URL
        sample_url = generate_sample_evidence("image", event.object_id)
        create_incident_evidence(
            db,
            IncidentEvidence(
                incident_id=saved_incident.id,
                evidence_type="image",
                url=sample_url,
                captured_at=event.occurred_at,
            ),
        )

    # Attach vehicle crop if plate text exists
    if event.plate_text:
        crop_url = generate_sample_evidence("plate_crop", event.object_id)
        create_incident_evidence(
            db,
            IncidentEvidence(
                incident_id=saved_incident.id,
                evidence_type="plate_crop",
                url=crop_url,
                captured_at=event.occurred_at,
            ),
        )

    try:
        import asyncio
        from app.services.websocket_manager import ws_manager
        detail_resp = _incident_to_detail_response(saved_incident)
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(ws_manager.broadcast_incident(detail_resp.model_dump()))
    except Exception:
        pass

    return saved_incident



def list_incidents(
    db: Session,
    status: Optional[str] = None,
    incident_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> PaginatedIncidentResponse:
    total, items = get_incidents(
        db, status=status, incident_type=incident_type, limit=limit, offset=offset
    )
    return PaginatedIncidentResponse(
        total=total,
        limit=limit,
        offset=offset,
        items=[_incident_to_response(item) for item in items],
    )


def get_incident_detail(db: Session, incident_id: UUID) -> Optional[IncidentDetailResponse]:
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        return None
    return _incident_to_detail_response(incident)


def review_incident(
    db: Session, incident_id: UUID, payload: IncidentUpdate
) -> Optional[IncidentDetailResponse]:
    incident = get_incident_by_id(db, incident_id)
    if not incident:
        return None

    updates = payload.model_dump(exclude_unset=True)
    if updates:
        incident = update_incident(db, incident, updates)

    return _incident_to_detail_response(incident)
