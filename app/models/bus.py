import uuid
from sqlalchemy import Column, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Bus(Base):
    __tablename__ = "buses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    registration_number = Column(Text, unique=True, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())