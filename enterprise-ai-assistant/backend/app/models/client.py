import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from app.core.database import Base

class ClientDB(Base):
    __tablename__ = "clients"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    plan_tier = Column(String(50), nullable=True, default="standard")
    settings = Column(JSON, nullable=True, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
