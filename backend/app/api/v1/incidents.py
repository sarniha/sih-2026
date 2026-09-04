from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.security import verify_service_token

from app.db.session import get_db
from app.schemas.incident import (
    IncidentCreate,
    IncidentDetailResponse,
    IncidentUpdate,
    PaginatedIncidentResponse,
)
from app.services.incident_service import (
    create_manual_case,
    get_incident_detail,
    list_incidents,
    review_incident,
)

router = APIRouter()


@router.get("/incidents", response_model=PaginatedIncidentResponse)
def get_incidents_endpoint(
    status: Optional[str] = Query(None),
    incident_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    return list_incidents(
        db=db,
        status=status,
        incident_type=incident_type,
        limit=limit,
        offset=offset,
    )


@router.get("/incidents/{incident_id}", response_model=IncidentDetailResponse)
def get_incident_detail_endpoint(incident_id: UUID, db: Session = Depends(get_db)):
    detail = get_incident_detail(db, incident_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Incident not found")
    return detail


@router.post("/incidents", response_model=IncidentDetailResponse, status_code=201)
def create_incident_endpoint(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
):
    return create_manual_case(db, payload)


@router.patch(
    "/incidents/{incident_id}",
    response_model=IncidentDetailResponse,
    dependencies=[Depends(verify_service_token)],
)
def review_incident_endpoint(
    incident_id: UUID,
    payload: IncidentUpdate,
    db: Session = Depends(get_db),
):
    updated = review_incident(db, incident_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Incident not found")
    return updated