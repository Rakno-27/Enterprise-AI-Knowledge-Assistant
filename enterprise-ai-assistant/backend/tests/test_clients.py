import os
import sys
import tempfile
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


def test_client_model_creation_and_fields():
    """Verify ClientDB model instantiation, defaults, and attributes."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # Create a client
        client = ClientDB(
            name="Acme Corp",
            slug="acme-corp",
            plan_tier="enterprise",
            settings={"theme": "dark", "max_users": 100}
        )
        db.add(client)
        db.commit()
        db.refresh(client)

        assert client.id is not None
        assert client.name == "Acme Corp"
        assert client.slug == "acme-corp"
        assert client.plan_tier == "enterprise"
        assert client.settings["theme"] == "dark"
        assert client.is_active is True
        assert client.created_at is not None

        # Verify querying by slug
        found = db.query(ClientDB).filter(ClientDB.slug == "acme-corp").first()
        assert found is not None
        assert found.id == client.id

    finally:
        db.close()


def test_alembic_migration_upgrade_and_downgrade_clients():
    """Verify applying the clients migration on top of baseline schema and rolling it back."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp_db:
        tmp_db_path = tmp_db.name

    tmp_url = f"sqlite:///{tmp_db_path.replace(os.sep, '/')}"

    original_url = settings.DATABASE_URL
    settings.DATABASE_URL = tmp_url

    try:
        alembic_ini_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "alembic.ini"))
        alembic_cfg = Config(alembic_ini_path)

        # 1. Upgrade to baseline
        command.upgrade(alembic_cfg, "8bb75ed5d2ff")
        engine = create_engine(tmp_url)
        inspector = inspect(engine)
        assert "clients" not in inspector.get_table_names()

        # 2. Upgrade to head (f7fcba2903da)
        command.upgrade(alembic_cfg, "head")
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        assert "clients" in tables
        assert {"users", "documents", "conversations", "chat_messages", "clients", "alembic_version"}.issubset(tables)

        # Verify columns in clients table
        client_cols = {c["name"] for c in inspector.get_columns("clients")}
        expected_cols = {"id", "name", "slug", "plan_tier", "settings", "created_at", "is_active"}
        assert expected_cols.issubset(client_cols)

        # 3. Downgrade back to baseline
        command.downgrade(alembic_cfg, "8bb75ed5d2ff")
        inspector = inspect(engine)
        assert "clients" not in inspector.get_table_names()
        assert {"users", "documents", "conversations", "chat_messages"}.issubset(set(inspector.get_table_names()))

    finally:
        settings.DATABASE_URL = original_url
        if os.path.exists(tmp_db_path):
            try:
                os.remove(tmp_db_path)
            except Exception:
                pass
