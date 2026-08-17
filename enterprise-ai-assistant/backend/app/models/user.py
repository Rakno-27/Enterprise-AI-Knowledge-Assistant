from sqlalchemy import Column, String, DateTime
from datetime import datetime
from app.core.database import Base

class UserDB(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True) # supports Auth0 user ID strings
    email = Column(String, unique=True, index=True, nullable=True)
    role = Column(String, nullable=True, default="user")
    created_at = Column(DateTime, default=datetime.utcnow)
