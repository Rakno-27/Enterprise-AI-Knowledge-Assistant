from app.core.database import Base
from app.models.client import ClientDB
from app.models.user import UserDB
from app.models.document import DocumentDB
from app.models.chat import ConversationDB, ChatMessageDB

# For auto table creation imports
__all__ = ["Base", "ClientDB", "UserDB", "DocumentDB", "ConversationDB", "ChatMessageDB"]
