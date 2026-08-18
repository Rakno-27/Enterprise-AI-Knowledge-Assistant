import os
import sys
import tempfile
import pytest
from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from alembic.runtime.migration import MigrationContext

# Add backend to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.core.config import settings

BASELINE_REV = "8bb75ed5d2ff"


def test_alembic_baseline_migration_upgrade_and_downgrade():
    """Verify that Alembic can apply the baseline migration from scratch and roll it back cleanly."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    tmp_url = f"sqlite:///{tmp_db_path.replace(os.sep, '/')}"

    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = tmp_url

    try:
        alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg = Config(alembic_ini_path)

        # 1. Upgrade from empty to baseline
        command.upgrade(alembic_cfg, BASELINE_REV)

        engine = create_engine(tmp_url)
        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            assert ctx.get_current_revision() == BASELINE_REV

        inspector = inspect(engine)
        tables = set(inspector.get_table_names())

        expected_tables = {"users", "documents", "conversations", "chat_messages", "alembic_version"}
        assert expected_tables.issubset(tables), f"Missing tables after upgrade: {expected_tables - tables}"

        # Verify columns in users
        user_cols = {c["name"] for c in inspector.get_columns("users")}
        assert {"id", "email", "role", "created_at"}.issubset(user_cols)

        # Verify columns in documents
        doc_cols = {c["name"] for c in inspector.get_columns("documents")}
        assert {"id", "filename", "file_type", "size_bytes", "uploaded_at", "chunks_count", "status", "error_message", "user_id"}.issubset(doc_cols)

        # Verify columns in conversations
        conv_cols = {c["name"] for c in inspector.get_columns("conversations")}
        assert {"id", "title", "user_id", "created_at"}.issubset(conv_cols)

        # Verify columns in chat_messages
        msg_cols = {c["name"] for c in inspector.get_columns("chat_messages")}
        assert {"id", "conversation_id", "role", "content", "sources", "latency", "token_count", "model_used", "timestamp"}.issubset(msg_cols)

        # 2. Downgrade to base
        command.downgrade(alembic_cfg, "base")

        with engine.connect() as conn:
            ctx = MigrationContext.configure(conn)
            assert ctx.get_current_revision() is None

        inspector = inspect(engine)
        remaining_tables = set(inspector.get_table_names()) - {"alembic_version"}
        assert len(remaining_tables) == 0, f"Tables remained after downgrade: {remaining_tables}"

    finally:
        settings.DATABASE_URL = original_url
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass


def test_alembic_stamp_on_existing_database():
    """Verify that stamping an existing database establishes the revision without altering existing data."""
    alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg = Config(alembic_ini_path)

    # Stamp database to head
    command.stamp(alembic_cfg, "head")

    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        current_rev = ctx.get_current_revision()
        assert current_rev is not None


def test_alembic_upgrade_is_idempotent():
    """Verify that running upgrade('head') when already at head is safe and idempotent."""
    alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
    alembic_cfg = Config(alembic_ini_path)

    command.upgrade(alembic_cfg, "head")

    engine = create_engine(settings.DATABASE_URL)
    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        assert ctx.get_current_revision() is not None
