import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Trip(Base):
    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    source = Column(Text, nullable=True)  # "live" or "recorded:<filename>"
    created_at = Column(DateTime(timezone=True), server_default=func.now())