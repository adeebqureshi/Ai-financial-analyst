"""
Authentication Database

SQLAlchemy engine/session management for the authentication store.

Design Decisions:
    - **SQLite by default**: ``AUTH_DATABASE_URL`` defaults to a local SQLite
      file so the stack runs with zero infrastructure. Point it at PostgreSQL
      (``postgresql+psycopg://...``) in production.
    - **Engines cached per URL**: Avoids re-creating connection pools and
      keeps SQLite file handles stable across requests/tests.
    - **Schema created lazily**: ``init_db()`` is invoked on first use; the
      schema is created with ``Base.metadata.create_all`` (no migration
      framework is introduced for this scope).
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


def init_db(settings: Settings) -> None:
    """
    Create the authentication schema if it does not already exist.

    Safe to call repeatedly; table creation is idempotent.
    """
    # Import for model registration side effects.
    from app.auth import models  # noqa: F401

    engine = get_engine(settings)

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