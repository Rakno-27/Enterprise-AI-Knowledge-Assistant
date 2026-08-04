from app.core.database import Base
from app.models.document import DocumentDB
from app.models.chat import ChatMessageDB

# For table creation imports
__all__ = ["Base", "DocumentDB", "ChatMessageDB"]
