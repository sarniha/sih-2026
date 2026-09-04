import uuid
from sqlalchemy import Column, Text, Numeric, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geography
from app.db.base import Base
from sqlalchemy import CheckConstraint

class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('pothole','waterlogging','signboard_damage','zebra_crossing_issue','traffic','anpr','hit_run')",
            name="ck_events_event_type",
        ),
        CheckConstraint("confidence BETWEEN 0 AND 1", name="ck_events_confidence"),
        CheckConstraint(
            "severity IN ('low','medium','high')", name="ck_events_severity"
        ),
        CheckConstraint(
            "status IN ('stored','reviewed','resolved','false_positive')",
            name="ck_events_status",
        ),
    )


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(Text, nullable=False)
    trip_id = Column(UUID(as_uuid=True), ForeignKey("trips.id"), nullable=False)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    camera_id = Column(UUID(as_uuid=True), ForeignKey("cameras.id"), nullable=True)
    object_id = Column(Text, nullable=True)
    confidence = Column(Numeric(4, 3), nullable=False)
    bbox = Column(JSONB, nullable=True)
    location = Column(Geography(geometry_type="POINT", srid=4326), nullable=True)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    severity = Column(Text, nullable=True)
    plate_text = Column(Text, nullable=True)
    plate_confidence = Column(Numeric(4, 3), nullable=True)
    evidence_url = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default="stored")
    metadata_ = Column("metadata", JSONB, nullable=True)