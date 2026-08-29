"""
Authentication Database

SQLAlchemy engine/session management for the authentication store.

Design Decisions:
    - **SQLite by default**: ``AUTH_DATABASE_URL`` defaults to a local SQLite
      file so the stack runs with zero infrastructure. Point it at PostgreSQL
      (``postgresql+psycopg://...``) in production.
    - **Engines cached per URL**: Avoids re-creating connection pools and
      keeps SQLite file handles stable across requests/tests.
    - **Schema managed by Alembic migrations in production**: ``init_db()`` runs
      migrations on PostgreSQL; on SQLite it falls back to ``create_all`` for
      zero-config development and tests.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import Settings
from app.infrastructure.postgres import create_db_engine


class Base(DeclarativeBase):
    """Declarative base for authentication ORM models."""


_engines: dict[str, Engine] = {}


def _engine_for(database_url: str) -> Engine:
    """Build (and cache) an engine for the given database URL."""
    engine = _engines.get(database_url)
    if engine is not None:
        return engine

    if database_url.startswith("sqlite:///"):
        db_path = database_url.removeprefix("sqlite:///")

        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # create_db_engine handles SQLite (StaticPool for :memory:, cross-thread
    # file access) and PostgreSQL (pooled, pre-ping, recycled) alike.
    engine = create_db_engine(database_url)
    _engines[database_url] = engine
    return engine


def get_engine(settings: Settings) -> Engine:
    """Return the engine for the configured authentication database."""
    return _engine_for(settings.auth_database_url)


def dispose_all_engines() -> None:
    """Dispose every cached auth engine (called on application shutdown)."""
    engines = list(_engines.values())
    _engines.clear()
    for engine in engines:
        try:
            engine.dispose()
        except Exception:  # pragma: no cover - shutdown must never raise
            pass


def _is_postgresql(database_url: str) -> bool:
    """Check if the database URL is for PostgreSQL."""
    return database_url.startswith("postgresql")


def run_migrations(database_url: str) -> None:
    """
    Run Alembic migrations for the authentication database.

    Only executes on PostgreSQL; on SQLite this is a no-op since
    ``create_all`` handles schema creation for development/tests.
    """
    if not _is_postgresql(database_url):
        return

    try:
        from alembic import command
        from alembic.config import Config

        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", database_url)
        # Override the auth section URL
        alembic_cfg.set_section_option("alembic_auth", "sqlalchemy.url", database_url)

        command.upgrade(alembic_cfg, "head")
    except Exception as exc:  # pragma: no cover - migration failures should be visible
        raise RuntimeError(f"Failed to run authentication database migrations: {exc}") from exc


def init_db(settings: Settings) -> None:
    """
    Initialize the authentication database schema.

    On PostgreSQL: runs Alembic migrations to bring schema to head.
    On SQLite: uses ``create_all`` for zero-config development and tests.

    Safe to call repeatedly; both operations are idempotent.
    """
    # Import for model registration side effects.
    from app.auth import models  # noqa: F401

    engine = get_engine(settings)
    database_url = settings.auth_database_url

    if _is_postgresql(database_url):
        run_migrations(database_url)
    else:
        Base.metadata.create_all(bind=engine)


def get_db_session(settings: Settings) -> Iterator[Session]:
    """
    Yield an authentication database session.

    The schema is ensured before the first session is handed out so the API
    works immediately after startup without a separate migration step.

    Note:
        This is a plain generator, deliberately free of FastAPI/API-package
        imports to avoid circular imports. Use the ``get_auth_db`` dependency
        in :mod:`app.auth.dependencies` inside route signatures.
    """
    init_db(settings)

    factory = sessionmaker(
        bind=get_engine(settings),
        autoflush=False,
        expire_on_commit=False,
    )

    session = factory()

    try:
        yield session
    finally:
        session.close()