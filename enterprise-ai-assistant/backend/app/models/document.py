from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from app.core.database import Base

class DocumentDB(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    chunks_count = Column(Integer, default=0)
