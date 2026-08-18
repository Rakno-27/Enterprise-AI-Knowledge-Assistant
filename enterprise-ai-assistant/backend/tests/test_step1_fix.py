"""
Step 1 Verification Test — ChatMessageDB persistence fix.

Verifies that:
1. generate_response() with a session_id writes a ConversationDB row whose id == session_id.
2. The user message is stored with conversation_id == session_id.
3. The assistant message is stored with conversation_id == session_id.
4. get_session_history() returns those two messages in correct order.
5. A second call with the same session_id reuses the existing conversation (idempotent).
6. A call WITHOUT session_id persists nothing (existing Phase 1 behavior preserved).
"""
import pytest
import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Bootstrap: use an in-memory SQLite DB so the test is self-contained
# ---------------------------------------------------------------------------
import sys, os
# Make sure the backend package is importable regardless of cwd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base
from app.models.user import UserDB
from app.models.document import DocumentDB
from app.models.chat import ConversationDB, ChatMessageDB
from app.services.chat_service import ChatService
from app.schemas.chat import ChatCompletionRequest, ChatMessage

# In-memory SQLite engine (test-isolated, not shared with real DB)
TEST_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=TEST_ENGINE)

@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables fresh before each test and tear down after."""
    Base.metadata.create_all(bind=TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=TEST_ENGINE)

def make_request(session_id=None, message="What is the security policy?"):
    return ChatCompletionRequest(
        messages=[ChatMessage(role="user", content=message)],
        model="gpt-4o-mini",
        use_rag=False,    # disable RAG so test doesn't need Qdrant/OpenAI
        session_id=session_id,
    )

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_messages_persisted_with_correct_conversation_id():
    """User and assistant messages must be stored with conversation_id == session_id."""
    db = TestSessionLocal()
    service = ChatService()
    session_id = "test-session-abc"

    try:
        await service.generate_response(db, make_request(session_id=session_id))

        # 1. Conversation row must exist
        conv = db.query(ConversationDB).filter(ConversationDB.id == session_id).first()
        assert conv is not None, "ConversationDB row was not created"
        assert conv.id == session_id

        # 2. Two messages must be stored
        msgs = (
            db.query(ChatMessageDB)
            .filter(ChatMessageDB.conversation_id == session_id)
            .order_by(ChatMessageDB.timestamp.asc())
            .all()
        )
        assert len(msgs) == 2, f"Expected 2 messages, got {len(msgs)}"

        # 3. Roles must be in order
        assert msgs[0].role == "user"
        assert msgs[1].role == "assistant"

        # 4. Content must be non-empty
        assert msgs[0].content == "What is the security policy?"
        assert len(msgs[1].content) > 0

        # 5. conversation_id FK must be correct on both
        assert msgs[0].conversation_id == session_id
        assert msgs[1].conversation_id == session_id

    finally:
        db.close()


@pytest.mark.asyncio
async def test_get_session_history_returns_messages():
    """get_session_history must return the persisted messages via conversation_id filter."""
    db = TestSessionLocal()
    service = ChatService()
    session_id = "test-session-history"

    try:
        await service.generate_response(db, make_request(session_id=session_id, message="Hello"))
        history = await service.get_session_history(db, session_id)

        assert len(history) == 2
        assert history[0].role == "user"
        assert history[0].content == "Hello"
        assert history[1].role == "assistant"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_second_call_reuses_existing_conversation():
    """A second generate_response with the same session_id must NOT create a duplicate ConversationDB row."""
    db = TestSessionLocal()
    service = ChatService()
    session_id = "test-session-reuse"

    try:
        await service.generate_response(db, make_request(session_id=session_id, message="First message"))
        await service.generate_response(db, make_request(session_id=session_id, message="Second message"))

        # Only one conversation row
        conv_count = db.query(ConversationDB).filter(ConversationDB.id == session_id).count()
        assert conv_count == 1, f"Expected 1 conversation row, got {conv_count}"

        # Four messages total (2 turns × 2 messages each)
        msg_count = db.query(ChatMessageDB).filter(ChatMessageDB.conversation_id == session_id).count()
        assert msg_count == 4, f"Expected 4 messages, got {msg_count}"
    finally:
        db.close()


@pytest.mark.asyncio
async def test_no_session_id_persists_nothing():
    """When session_id is None, no DB rows must be written — Phase 1 behavior preserved."""
    db = TestSessionLocal()
    service = ChatService()

    try:
        await service.generate_response(db, make_request(session_id=None))

        conv_count = db.query(ConversationDB).count()
        msg_count = db.query(ChatMessageDB).count()
        assert conv_count == 0, f"Expected 0 conversations, got {conv_count}"
        assert msg_count == 0, f"Expected 0 messages, got {msg_count}"
    finally:
        db.close()
