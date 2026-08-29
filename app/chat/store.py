"""
Chat Store
==========

The persistence layer for chat sessions and messages. It is the single source
of truth for conversations so chats survive restarts and are shared across
multiple workers/containers.

Design Decisions:
    - **Strict ownership isolation**: Every operation is scoped by ``owner_id``
      (the authenticated user id, ``None`` for the anonymous development
      bucket). One user can never read, list, or mutate another user's
      conversations; foreign sessions behave as if they do not exist.
    - **Concurrency safety**: Sessions are "get-or-create" with a database
      ``UNIQUE (owner_id, session_id)`` constraint, so simultaneous first
      writes from multiple workers cannot create duplicates (an ``IntegrityError``
      is retried as a read).
    - **Pagination**: List operations return ``(items, total)`` and are ordered
      deterministically (by id / created_at).
    - **Retention/cleanup**: ``purge_expired`` removes idle sessions (and their
      messages) older than the retention window.
    - **Optional Redis cache**: When a cache is provided and healthy, recent
      session context is cached to reduce read load; the database stays the
      canonical store.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import timedelta
from typing import Any, Iterator

from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.chat.cache import ChatSessionCache
from app.chat.database import ChatPersistenceError, get_engine, init_db
from app.chat.models import ChatMessage, ChatSession, _utcnow_naive, to_aware_utc


class ChatStore:
    """Ownership-scoped, persistent chat session and message storage."""

    def __init__(
        self,
        database_url: str,
        *,
        cache: ChatSessionCache | None = None,
        retention_days: int = 30,
    ) -> None:
        self._database_url = database_url
        self._cache = cache
        self._retention_days = retention_days

        init_db(database_url)

        self._sessionmaker = sessionmaker(
            bind=get_engine(database_url),
            autoflush=False,
            expire_on_commit=False,
        )

    # ──────────────────────────────────────────────────────────────────────
    # Internal helpers
    # ──────────────────────────────────────────────────────────────────────

    @contextmanager
    def _session(self) -> Iterator[Session]:
        """Yield an isolated database session that is always closed."""
        session = self._sessionmaker()
        try:
            yield session
        finally:
            session.close()

    @staticmethod
    def _owner_cond(owner_id: str | None):
        """Build the SQLAlchemy owner predicate (NULL-guarded)."""
        if owner_id is None:
            return ChatSession.owner_id.is_(None)
        return ChatSession.owner_id == owner_id

    def _get_or_create(
        self,
        db: Session,
        owner_id: str | None,
        session_id: str,
        *,
        title: str | None = None,
    ) -> ChatSession:
        row = db.scalar(
            select(ChatSession).where(
                self._owner_cond(owner_id),
                ChatSession.session_id == session_id,
            )
        )

        if row is not None:
            return row

        row = ChatSession(
            owner_id=owner_id,
            session_id=session_id,
            title=title,
        )
        db.add(row)

        try:
            db.commit()
        except IntegrityError:
            # Lost the race to another writer; read the winning row instead.
            db.rollback()
            row = db.scalar(
                select(ChatSession).where(
                    self._owner_cond(owner_id),
                    ChatSession.session_id == session_id,
                )
            )
            if row is None:
                raise ChatPersistenceError(
                    f"Failed to create chat session {session_id!r}."
                ) from None

        db.refresh(row)
        return row

    def _load_session(
        self,
        db: Session,
        owner_id: str | None,
        session_id: str,
    ) -> ChatSession | None:
        return db.scalar(
            select(ChatSession).where(
                self._owner_cond(owner_id),
                ChatSession.session_id == session_id,
            )
        )

    @staticmethod
    def _session_dict(session: ChatSession) -> dict[str, Any]:
        return {
            "session_id": session.session_id,
            "title": session.title,
            "metadata": session.metadata_json or {},
            "created_at": to_aware_utc(session.created_at),
            "updated_at": to_aware_utc(session.updated_at),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Write operations
    # ──────────────────────────────────────────────────────────────────────

    def save_turn(
        self,
        owner_id: str | None,
        session_id: str,
        *,
        user_message: str,
        assistant_message: str,
        user_meta: dict[str, Any] | None = None,
        assistant_meta: dict[str, Any] | None = None,
        session_meta: dict[str, Any] | None = None,
        title: str | None = None,
    ) -> None:
        """
        Persist one conversational turn (user message + assistant reply).

        The session is created on first write. ``assistant_meta`` should carry
        the ``query`` and ``tickers`` so follow-up context can be restored.
        """
        with self._session() as db:
            session = self._get_or_create(db, owner_id, session_id, title=title)

            if session_meta and session.title is None and title is None:
                session.title = session_meta.get("title") or session.title

            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="user",
                    content=user_message,
                    metadata_json=dict(user_meta or {}),
                )
            )
            db.add(
                ChatMessage(
                    session_id=session.id,
                    role="assistant",
                    content=assistant_message,
                    metadata_json=dict(assistant_meta or {}),
                )
            )

            db.execute(
                update(ChatSession)
                .where(ChatSession.id == session.id)
                .values(updated_at=_utcnow_naive())
            )
            db.commit()

        self._update_cache(owner_id, session_id, assistant_meta)

    def delete_session(self, owner_id: str | None, session_id: str) -> bool:
        """Delete a session (and its messages) if owned by ``owner_id``."""
        with self._session() as db:
            session = self._load_session(db, owner_id, session_id)

            if session is None:
                return False

            db.execute(
                delete(ChatMessage).where(ChatMessage.session_id == session.id)
            )
            db.delete(session)
            db.commit()

        if self._cache is not None:
            self._cache.invalidate(owner_id, session_id)

        return True

    # ──────────────────────────────────────────────────────────────────────
    # Read operations
    # ──────────────────────────────────────────────────────────────────────

    def get_session_state(self, owner_id: str | None, session_id: str) -> dict[str, Any] | None:
        """
        Return the most recent turn's context (``query``, ``tickers``,
        ``answer``) for follow-up resolution, or ``None``.

        This is what lets multi-turn follow-ups survive restarts and span
        multiple workers.
        """
        if self._cache is not None:
            cached = self._cache.get_context(owner_id, session_id)
            if cached is not None:
                return cached

        with self._session() as db:
            session = self._load_session(db, owner_id, session_id)

            if session is None:
                return None

            message = db.scalar(
                select(ChatMessage)
                .where(
                    ChatMessage.session_id == session.id,
                    ChatMessage.role == "assistant",
                )
                .order_by(ChatMessage.id.desc())
                .limit(1)
            )

            if message is None:
                return None

            meta = message.metadata_json or {}
            return {
                "tickers": meta.get("tickers") or [],
                "query": meta.get("query") or "",
                "answer": message.content,
            }

    def get_session(self, owner_id: str | None, session_id: str) -> dict[str, Any] | None:
        """Return the owned session as a dict, or ``None``."""
        with self._session() as db:
            session = self._load_session(db, owner_id, session_id)

            if session is None:
                return None

            return self._session_dict(session)

    def list_sessions(
        self,
        owner_id: str | None,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return ``(sessions, total)`` for the owner, newest-first."""
        page = max(page, 1)
        page_size = min(max(page_size, 1), 100)

        with self._session() as db:
            total = db.scalar(
                select(func.count(ChatSession.id)).where(self._owner_cond(owner_id))
            )

            rows = db.scalars(
                select(ChatSession)
                .where(self._owner_cond(owner_id))
                .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()

            return [self._session_dict(row) for row in rows], total or 0

    def list_messages(
        self,
        owner_id: str | None,
        session_id: str,
        *,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[dict[str, Any]], int]:
        """Return ``(messages, total)`` for an owned session, oldest-first."""
        page = max(page, 1)
        page_size = min(max(page_size, 1), 200)

        with self._session() as db:
            session = self._load_session(db, owner_id, session_id)

            if session is None:
                # Foreign/unknown session is indistinguishable from "no data".
                return [], 0

            total = db.scalar(
                select(func.count(ChatMessage.id)).where(
                    ChatMessage.session_id == session.id
                )
            )

            rows = db.scalars(
                select(ChatMessage)
                .where(ChatMessage.session_id == session.id)
                .order_by(ChatMessage.id.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            ).all()

            messages = [
                {
                    "id": row.id,
                    "role": row.role,
                    "content": row.content,
                    "metadata": row.metadata_json or {},
                    "created_at": to_aware_utc(row.created_at),
                }
                for row in rows
            ]

            return messages, total or 0

    def purge_expired(
        self,
        retention_days: int | None = None,
        *,
        owner_id: str | None = None,
    ) -> int:
        """
        Delete idle sessions (and their messages) older than the retention
        window. Returns the number of sessions removed.

        When ``owner_id`` is ``None`` this purges every owner's expired data;
        pass an explicit owner to scope cleanup to a single user.
        """
        days = max(retention_days if retention_days is not None else self._retention_days, 0)
        cutoff = _utcnow_naive() - timedelta(days=days)

        with self._session() as db:
            stmt = select(ChatSession).where(ChatSession.updated_at < cutoff)

            if owner_id is not None:
                stmt = stmt.where(self._owner_cond(owner_id))

            sessions = list(db.scalars(stmt).all())

            if not sessions:
                return 0

            ids = [s.id for s in sessions]

            db.execute(delete(ChatMessage).where(ChatMessage.session_id.in_(ids)))
            db.execute(delete(ChatSession).where(ChatSession.id.in_(ids)))
            db.commit()

            return len(ids)

    # ──────────────────────────────────────────────────────────────────────
    # Cache bridge
    # ──────────────────────────────────────────────────────────────────────

    def _update_cache(
        self,
        owner_id: str | None,
        session_id: str,
        assistant_meta: dict[str, Any] | None,
    ) -> None:
        if self._cache is None or not assistant_meta:
            return

        context = {
            "tickers": assistant_meta.get("tickers") or [],
            "query": assistant_meta.get("query") or "",
            "answer": assistant_meta.get("answer") or "",
        }
        self._cache.set_context(owner_id, session_id, context)