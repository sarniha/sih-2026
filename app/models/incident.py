import uuid
from sqlalchemy import Column, Text, Numeric, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from geoalchemy2 import Geography
from app.db.base import Base


class Incident(Base):
    __tablename__ = "incidents"
    __table_args__ = (
        CheckConstraint(
            "incident_type IN ('suspected_collision', 'suspected_hit_and_run')",
            name="ck_incidents_type",
        ),
        CheckConstraint(
            "status IN ('open', 'under_review', 'closed', 'dismissed')",
            name="ck_incidents_status",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False)
    incident_type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, server_default="open")
    suspected_plate = Column(Text, nullable=True)
    suspected_plate_confidence = Column(Numeric(4, 3), nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    notes = Column(Text, nullable=True)

    primary_event = relationship("Event")
    evidence_items = relationship("IncidentEvidence", back_populates="incident", cascade="all, delete-orphan")
