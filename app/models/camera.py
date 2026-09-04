import uuid
from sqlalchemy import Column, Text, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bus_id = Column(UUID(as_uuid=True), ForeignKey("buses.id"), nullable=False)
    position = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())