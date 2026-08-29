"""
Chat Persistence Database
=========================

SQLAlchemy engine/session management for the persistent chat conversation
store.

Design Decisions:
    - **PostgreSQL in production, SQLite in development**: ``chat_database_url``
      defaults to a local SQLite file so the stack runs with zero
      infrastructure locally. Point it at PostgreSQL
      (``postgresql+psycopg://...``) in production so conversations survive
      restarts and are shared across multiple workers/containers.
    - **Engines cached per URL**: Pooling is reused across instances and the
      SQLite file handle stays stable across requests/tests.
    - **Schema created lazily**: ``init_db()`` is invoked on first use so the
      API works immediately after startup without a separate migration step.
    - **Adapter-aware creation**: ``create_all`` is wrapped so a full
      ``CREATE TABLE`` idempotence check is safe on both PostgreSQL and SQLite.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import lru_cache
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.infrastructure.postgres import create_db_engine


class ChatPersistenceError(Exception):
    """Raised when the chat store cannot persist or read a conversation."""


class Base(DeclarativeBase):
    """Declarative base for chat persistence ORM models."""


def _tune_sqlite(engine: Engine, database_url: str) -> Engine:
    """
    Apply SQLite pragmas suitable for a threaded web server.

    - WAL journal mode allows concurrent readers during writes (multi-worker
      friendly for a file-based development database).
    - A generous ``busy_timeout`` turns transient lock contention into a short
      wait instead of an immediate ``OperationalError``.
    """
    if ":memory:" in database_url:
        return engine

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection, _record):  # pragma: no cover - sqlite-specific
        cursor = dbapi_connection.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.execute("PRAGMA foreign_keys=ON")
        finally:
            cursor.close()

    return engine


_engines: dict[str, Engine] = {}


@lru_cache(maxsize=8)
def _engine_for(database_url: str) -> Engine:
    """Build (and cache) an engine for the given database URL."""
    if database_url.startswith("sqlite:///"):
        db_path = database_url.removeprefix("sqlite:///")

        if db_path and db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    # create_db_engine handles SQLite (StaticPool for :memory:, cross-thread
    # file access) and PostgreSQL (pooled, pre-ping, recycled) alike.
    engine = create_db_engine(database_url)

    if database_url.startswith("sqlite:///"):
        _tune_sqlite(engine, database_url)

    _engines[database_url] = engine

    return engine


def get_engine(database_url: str) -> Engine:
    """Return the (cached) engine for the given database URL."""
    return _engine_for(database_url)


def dispose_engine(database_url: str) -> None:
    """Dispose (and forget) the cached engine for the given URL."""
    engine = _engines.pop(database_url, None)
    if engine is not None:
        try:
            engine.dispose()
        except Exception:  # pragma: no cover - shutdown must never raise
            pass
    _engine_for.cache_clear()


def dispose_all_engines() -> None:
    """Dispose every cached chat engine (called on application shutdown)."""
    engines = list(_engines.values())
    _engines.clear()
    _engine_for.cache_clear()
    for engine in engines:
        try:
            engine.dispose()
        except Exception:  # pragma: no cover
            pass


def init_db(database_url: str) -> None:
    """Create the chat schema if it does not already exist (idempotent)."""
    # Import for model registration side effects.
    from app.chat import models  # noqa: F401

    engine = get_engine(database_url)

    Base.metadata.create_all(bind=engine)


def get_db_session(database_url: str) -> Iterator[Session]:
    """
    Yield a chat database session.

    The schema is ensured before the first session is handed out so the API
    works immediately after startup without a separate migration step.

    Note:
        This is a plain generator, deliberately free of FastAPI/API-package
        imports to avoid circular imports. Service code should use a
        :class:`~app.chat.store.ChatStore` built from these primitives.
    """
    init_db(database_url)

    factory = sessionmaker(
        bind=get_engine(database_url),
        autoflush=False,
        expire_on_commit=False,
    )

    session = factory()

    try:
        yield session
    finally:
        session.close()