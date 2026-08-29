"""
Chat Persistence
================

Persistent, ownership-isolated storage for chat sessions and messages.

Modules:
    - ``database`` — SQLAlchemy engine/session management (SQLite dev /
      PostgreSQL production).
    - ``models``   — ``ChatSession`` and ``ChatMessage`` ORM models.
    - ``cache``    — Optional Redis-backed session-context cache.
    - ``store``    — ``ChatStore``: ownership-scoped persistence, pagination,
      retention/cleanup and concurrency-safe notes.

Import from the concrete submodules instead:::

    from app.chat.store import ChatStore
    from app.chat.cache import ChatSessionCache
    from app.chat.database import ChatPersistenceError
"""

from __future__ import annotations

__all__ = [
    "ChatPersistenceError",
    "ChatSessionCache",
    "ChatStore",
]