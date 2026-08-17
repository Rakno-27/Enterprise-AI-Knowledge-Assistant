from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON, Text
from datetime import datetime
import uuid
from app.core.database import Base

class ConversationDB(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, nullable=True)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessageDB(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), index=True, nullable=False)
    role = Column(String, nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # stores list of dicts (sources)
    latency = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    model_used = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
