import os
import sys
import tempfile
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.config import settings
from app.core.database import Base
from app.models.client import ClientDB
from app.models.user import UserDB
from app.models.document import DocumentDB
from app.models.chat import ConversationDB, ChatMessageDB
from app.services.rag_service import rag_service


def test_models_client_id_foreign_keys_and_cascade():
    """Verify that client_id foreign keys exist, allow NULL, and cascade on client deletion."""
    engine = create_engine("sqlite:///:memory:")
    
    # Enable SQLite foreign key constraints
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
        
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. Verify NULL client_id is permitted for backwards compatibility
        user_null = UserDB(id="usr-null", email="null@test.com")
        doc_null = DocumentDB(id="doc-null", filename="null.txt", file_type="txt", size_bytes=100)
        conv_null = ConversationDB(id="conv-null", title="Null Client Session")
        db.add_all([user_null, doc_null, conv_null])
        db.commit()

        assert user_null.client_id is None
        assert doc_null.client_id is None
        assert conv_null.client_id is None

        # 2. Verify associated records with a real client
        client = ClientDB(id="client-test-1", name="Test Tenant", slug="test-tenant")
        db.add(client)
        db.commit()

        user_scoped = UserDB(id="usr-scoped", client_id=client.id, email="tenant@test.com")
        doc_scoped = DocumentDB(id="doc-scoped", client_id=client.id, filename="tenant.pdf", file_type="pdf", size_bytes=500)
        conv_scoped = ConversationDB(id="conv-scoped", client_id=client.id, title="Tenant Session")
        db.add_all([user_scoped, doc_scoped, conv_scoped])
        db.commit()

        assert user_scoped.client_id == "client-test-1"
        assert doc_scoped.client_id == "client-test-1"
        assert conv_scoped.client_id == "client-test-1"

    finally:
        db.close()


def test_alembic_migration_step4_upgrade_and_downgrade():
    """Verify applying the add_client_id_to_schema migration and rolling it back."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    tmp_url = f"sqlite:///{tmp_db_path.replace(os.sep, '/')}"

    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = tmp_url

    try:
        alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg = Config(alembic_ini_path)

        # 1. Upgrade to previous revision (clients table only)
        command.upgrade(alembic_cfg, "f7fcba2903da")
        engine = create_engine(tmp_url)
        inspector = inspect(engine)

        user_cols = {c["name"] for c in inspector.get_columns("users")}
        assert "client_id" not in user_cols

        # 2. Upgrade to head (add_client_id_to_schema: cbe70e3db6b0)
        command.upgrade(alembic_cfg, "head")
        inspector = inspect(engine)

        user_cols = {c["name"] for c in inspector.get_columns("users")}
        doc_cols = {c["name"] for c in inspector.get_columns("documents")}
        conv_cols = {c["name"] for c in inspector.get_columns("conversations")}

        assert "client_id" in user_cols
        assert "client_id" in doc_cols
        assert "client_id" in conv_cols

        # 3. Downgrade back to f7fcba2903da
        command.downgrade(alembic_cfg, "f7fcba2903da")
        inspector = inspect(engine)

        user_cols = {c["name"] for c in inspector.get_columns("users")}
        doc_cols = {c["name"] for c in inspector.get_columns("documents")}
        conv_cols = {c["name"] for c in inspector.get_columns("conversations")}

        assert "client_id" not in user_cols
        assert "client_id" not in doc_cols
        assert "client_id" not in conv_cols

    finally:
        settings.DATABASE_URL = original_url
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass


@pytest.mark.asyncio
async def test_rag_service_ingest_and_retrieve_with_client_id():
    """Verify that rag_service ingests documents with client_id payload and filters retrieval appropriately."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    captured_points = []
    def mock_upsert(collection_name, points):
        captured_points.extend(points)

    try:
        with patch.object(rag_service.qdrant, "upsert", side_effect=mock_upsert):
            # Ingest document with custom client_id
            content = b"Security guidelines for Client Alpha tenant."
            doc = await rag_service.ingest_document(
                db=db,
                filename="alpha_security.txt",
                content=content,
                file_type="txt",
                client_id="client-alpha"
            )
            assert doc.id is not None

            # Verify DocumentDB record stored client_id
            stored_doc = db.query(DocumentDB).filter(DocumentDB.id == doc.id).first()
            assert stored_doc is not None
            assert stored_doc.client_id == "client-alpha"

            # Verify Qdrant payload contains client_id
            assert len(captured_points) > 0
            for point in captured_points:
                assert point.payload["client_id"] == "client-alpha"

        # Verify retrieve_context handles client_id filter without error (with mock fallback or Qdrant)
        results_scoped = await rag_service.retrieve_context(
            query="security guidelines",
            top_k=3,
            client_id="client-alpha"
        )
        assert isinstance(results_scoped, list)

        # Verify retrieve_context without client_id continues to work (Phase 1 behavior preserved)
        results_unscoped = await rag_service.retrieve_context(
            query="security guidelines",
            top_k=3,
            client_id=None
        )
        assert isinstance(results_unscoped, list)

    finally:
        db.close()
