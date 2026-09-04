from typing import Any, Dict, Optional, Tuple, List
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.incident import Incident
from app.models.incident_evidence import IncidentEvidence


def create_incident(db: Session, incident: Incident) -> Incident:
    """Insert a new incident into the database."""
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def create_incident_evidence(db: Session, evidence: IncidentEvidence) -> IncidentEvidence:
    """Insert a new evidence item linked to an incident."""
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


def get_incidents(
    db: Session,
    status: Optional[str] = None,
    incident_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> Tuple[int, List[Incident]]:
    """Query paginated incidents filtered by status or incident_type."""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.status == status)
    if incident_type:
        query = query.filter(Incident.incident_type == incident_type)

    total = query.count()
    items = query.order_by(Incident.occurred_at.desc()).offset(offset).limit(limit).all()
    return total, items


def get_incident_by_id(db: Session, incident_id: UUID) -> Optional[Incident]:
    """Retrieve single incident by ID with evidence items."""
    return db.query(Incident).filter(Incident.id == incident_id).first()


def update_incident(db: Session, incident: Incident, updates: Dict[str, Any]) -> Incident:
    """Update fields on an existing incident row."""
    for key, value in updates.items():
        if value is not None:
            setattr(incident, key, value)
    db.commit()
    db.refresh(incident)
    return incident
