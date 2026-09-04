import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class IncidentEvidence(Base):
    __tablename__ = "incident_evidence"
    __table_args__ = (
        CheckConstraint(
            "evidence_type IN ('image', 'vehicle_crop', 'plate_crop', 'video_clip')",
            name="ck_incident_evidence_type",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id"), nullable=False)
    evidence_type = Column(Text, nullable=False)
    url = Column(Text, nullable=False)
    captured_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    incident = relationship("Incident", back_populates="evidence_items")
