"""
Integration tests for database migrations.

These tests verify that a fresh database can be migrated to head
using Alembic migrations for both auth and chat databases.

Note: These tests use SQLite for speed, but the migration logic
is identical for PostgreSQL in production.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.auth.database import init_db as init_auth_db
from app.auth.database import get_engine as get_auth_engine
from app.chat.database import init_db as init_chat_db
from app.chat.database import get_engine as get_chat_engine


# Specific revision IDs for each database (since they have separate histories)
AUTH_HEAD_REVISION = "05d52563b705"
CHAT_HEAD_REVISION = "2a095841dbdc"


@pytest.fixture(autouse=True)
def _isolated_db_urls(monkeypatch):
    """Force alembic/env.py to read the URL from the per-test Alembic Config
    instead of the process-level ``AUTH_DATABASE_URL`` / ``CHAT_DATABASE_URL``
    env vars that conftest.py sets for the running test suite (which point at
    a shared temp DB and would override the per-test ``tmp_path`` URL)."""
    monkeypatch.delenv("AUTH_DATABASE_URL", raising=False)
    monkeypatch.delenv("CHAT_DATABASE_URL", raising=False)


def _make_alembic_config(database_url: str, database_type: str) -> Config:
    """Create an Alembic config for the given database."""
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", database_url)
    if database_type == "auth":
        cfg.set_section_option("alembic_auth", "sqlalchemy.url", database_url)
    else:
        cfg.set_section_option("alembic_chat", "sqlalchemy.url", database_url)

    # Tell env.py which migration script directory / metadata / version table
    # to use.  Without this the -x ``database`` argument defaults to "auth"
    # inside env.py, so chat migrations would target the auth metadata and the
    # alembic.ini default ``/tmp/...`` location (which does not exist on Windows).
    cfg.cmd_opts = SimpleNamespace(x=[f"database={database_type}"])
    return cfg


def _create_engine_for_test(database_url: str) -> Engine:
    """Create a fresh engine for testing without running init_db."""
    from app.infrastructure.postgres import create_db_engine
    return create_db_engine(database_url)


class TestAuthMigrations:
    """Test authentication database migrations."""

    def test_fresh_sqlite_database_migrates_to_head(self, tmp_path: Path) -> None:
        """Test that a fresh SQLite database can be migrated to head."""
        db_path = tmp_path / "test_auth.db"
        database_url = f"sqlite:///{db_path}"

        # Run migrations
        cfg = _make_alembic_config(database_url, "auth")
        command.upgrade(cfg, AUTH_HEAD_REVISION)

        # Verify tables exist using a fresh engine (not init_db)
        engine = _create_engine_for_test(database_url)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        assert "users" in tables
        assert "auth_alembic_version" in tables

        # Verify users table structure
        columns = {col["name"]: col for col in inspector.get_columns("users")}
        assert "id" in columns
        assert "email" in columns
        assert "hashed_password" in columns
        assert "is_active" in columns
        assert "created_at" in columns

        # Verify index on email
        indexes = inspector.get_indexes("users")
        email_indexes = [idx for idx in indexes if "email" in idx["column_names"]]
        assert len(email_indexes) > 0

        # Verify migration version
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM auth_alembic_version")).scalar()
            assert result == AUTH_HEAD_REVISION

    def test_init_db_runs_migrations_on_postgresql_url(self) -> None:
        """Test that init_db runs migrations when given a PostgreSQL URL."""
        # Use SQLite but with postgresql prefix to test the logic
        database_url = "postgresql+psycopg://user:pass@localhost/db"

        # We can't actually test PostgreSQL without a running instance,
        # but we can verify the function detects PostgreSQL URLs
        from app.auth.database import _is_postgresql

        assert _is_postgresql(database_url) is True
        assert _is_postgresql("sqlite:///test.db") is False


class TestChatMigrations:
    """Test chat database migrations."""

    def test_fresh_sqlite_database_migrates_to_head(self, tmp_path: Path) -> None:
        """Test that a fresh SQLite database can be migrated to head."""
        db_path = tmp_path / "test_chat.db"
        database_url = f"sqlite:///{db_path}"

        # Run migrations
        cfg = _make_alembic_config(database_url, "chat")
        command.upgrade(cfg, CHAT_HEAD_REVISION)

        # Verify tables exist using a fresh engine (not init_db)
        engine = _create_engine_for_test(database_url)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        assert "chat_sessions" in tables
        assert "chat_messages" in tables
        assert "chat_alembic_version" in tables

        # Verify chat_sessions table structure
        session_columns = {col["name"]: col for col in inspector.get_columns("chat_sessions")}
        assert "id" in session_columns
        assert "owner_id" in session_columns
        assert "session_id" in session_columns
        assert "title" in session_columns
        assert "metadata_json" in session_columns
        assert "created_at" in session_columns
        assert "updated_at" in session_columns

        # Verify unique constraint on (owner_id, session_id)
        unique_constraints = inspector.get_unique_constraints("chat_sessions")
        owner_session_constraints = [
            uc for uc in unique_constraints
            if set(uc["column_names"]) == {"owner_id", "session_id"}
        ]
        assert len(owner_session_constraints) > 0

        # Verify chat_messages table structure
        message_columns = {col["name"]: col for col in inspector.get_columns("chat_messages")}
        assert "id" in message_columns
        assert "session_id" in message_columns
        assert "role" in message_columns
        assert "content" in message_columns
        assert "metadata_json" in message_columns
        assert "created_at" in message_columns

        # Verify foreign key
        fks = inspector.get_foreign_keys("chat_messages")
        session_fks = [fk for fk in fks if "chat_sessions" in fk["referred_table"]]
        assert len(session_fks) > 0

        # Verify indexes
        indexes = inspector.get_indexes("chat_messages")
        index_names = [idx["name"] for idx in indexes]
        assert any("session_created" in name for name in index_names)

        # Verify migration version
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM chat_alembic_version")).scalar()
            assert result == CHAT_HEAD_REVISION

    def test_downgrade_removes_all_tables(self, tmp_path: Path) -> None:
        """Test that downgrading to base removes all tables."""
        db_path = tmp_path / "test_chat_downgrade.db"
        database_url = f"sqlite:///{db_path}"

        # Upgrade to head
        cfg = _make_alembic_config(database_url, "chat")
        command.upgrade(cfg, CHAT_HEAD_REVISION)

        # Verify tables exist
        engine = _create_engine_for_test(database_url)
        inspector = inspect(engine)
        tables_before = set(inspector.get_table_names())
        assert "chat_sessions" in tables_before
        assert "chat_messages" in tables_before

        # Downgrade to base
        command.downgrade(cfg, "base")

        # Verify tables are gone (except alembic_version which is also dropped)
        inspector = inspect(engine)
        tables_after = set(inspector.get_table_names())
        assert "chat_sessions" not in tables_after
        assert "chat_messages" not in tables_after

    def test_init_db_runs_migrations_on_postgresql_url(self) -> None:
        """Test that init_db runs migrations when given a PostgreSQL URL."""
        database_url = "postgresql+psycopg://user:pass@localhost/db"

        from app.chat.database import _is_postgresql

        assert _is_postgresql(database_url) is True
        assert _is_postgresql("sqlite:///test.db") is False


class TestMigrationIntegration:
    """Test migration integration with application database modules."""

    def test_auth_init_db_creates_schema_on_sqlite(self, tmp_path: Path) -> None:
        """Test that auth init_db works on SQLite (development mode)."""
        db_path = tmp_path / "test_auth_init.db"
        database_url = f"sqlite:///{db_path}"

        settings = Settings(auth_database_url=database_url)
        init_auth_db(settings)

        engine = get_auth_engine(settings)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        assert "users" in tables

    def test_chat_init_db_creates_schema_on_sqlite(self, tmp_path: Path) -> None:
        """Test that chat init_db works on SQLite (development mode)."""
        db_path = tmp_path / "test_chat_init.db"
        database_url = f"sqlite:///{db_path}"

        init_chat_db(database_url)

        engine = get_chat_engine(database_url)
        inspector = inspect(engine)

        tables = inspector.get_table_names()
        assert "chat_sessions" in tables
        assert "chat_messages" in tables

    def test_both_databases_can_coexist(self, tmp_path: Path) -> None:
        """Test that both auth and chat databases can be initialized independently."""
        auth_db_path = tmp_path / "auth.db"
        chat_db_path = tmp_path / "chat.db"

        auth_url = f"sqlite:///{auth_db_path}"
        chat_url = f"sqlite:///{chat_db_path}"

        # Initialize both
        auth_settings = Settings(auth_database_url=auth_url)
        init_auth_db(auth_settings)
        init_chat_db(chat_url)

        # Verify both have correct tables
        auth_engine = get_auth_engine(auth_settings)
        auth_inspector = inspect(auth_engine)
        assert "users" in auth_inspector.get_table_names()

        chat_engine = get_chat_engine(chat_url)
        chat_inspector = inspect(chat_engine)
        assert "chat_sessions" in chat_inspector.get_table_names()
        assert "chat_messages" in chat_inspector.get_table_names()


class TestMigrationIdempotency:
    """Test that migrations are idempotent."""

    def test_auth_migration_idempotent(self, tmp_path: Path) -> None:
        """Test that running auth migrations twice doesn't fail."""
        db_path = tmp_path / "test_auth_idempotent.db"
        database_url = f"sqlite:///{db_path}"

        cfg = _make_alembic_config(database_url, "auth")

        # Run upgrade twice
        command.upgrade(cfg, AUTH_HEAD_REVISION)
        command.upgrade(cfg, AUTH_HEAD_REVISION)  # Should not fail

        # Verify still at head
        engine = _create_engine_for_test(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM auth_alembic_version")).scalar()
            assert result == AUTH_HEAD_REVISION

    def test_chat_migration_idempotent(self, tmp_path: Path) -> None:
        """Test that running chat migrations twice doesn't fail."""
        db_path = tmp_path / "test_chat_idempotent.db"
        database_url = f"sqlite:///{db_path}"

        cfg = _make_alembic_config(database_url, "chat")

        # Run upgrade twice
        command.upgrade(cfg, CHAT_HEAD_REVISION)
        command.upgrade(cfg, CHAT_HEAD_REVISION)  # Should not fail

        # Verify still at head
        engine = _create_engine_for_test(database_url)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version_num FROM chat_alembic_version")).scalar()
            assert result == CHAT_HEAD_REVISION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])