from sqlalchemy import Column, String, Integer, DateTime
from datetime import datetime
from app.core.database import Base

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String, index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
