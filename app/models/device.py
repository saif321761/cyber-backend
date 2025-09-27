from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.core.db import Base

class Device(Base):
    __tablename__ = "devices"

    fcm_token = Column(String, primary_key=True, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
