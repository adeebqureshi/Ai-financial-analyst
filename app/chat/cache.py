from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatSessionCache:
    """In-process cache of recent chat-session context.

    The project runs a single backend worker, so a thread-safe in-process dict
    is sufficient and no external cache service is required. This replaces the
    previous Redis-backed implementation; when Redis was unreachable it already
    degraded to the database, so the persisted chat store remains the source of
    truth either way.
    """

    def __init__(self, redis_url: str = "", *, ttl_seconds: int = 300) -> None:
        # ``redis_url`` is accepted for backwards compatibility and ignored.
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, tuple[float, dict[str, Any]]] = {}

    @property
    def enabled(self) -> bool:
        """The in-process cache is always available."""
        return True

    def _key(self, owner_id: str | None, session_id: str) -> str:
        owner = owner_id or "anonymous"
        return f"chat:{owner}:{session_id}:context"

    def get_context(self, owner_id: str | None, session_id: str) -> dict[str, Any] | None:
        import time

        key = self._key(owner_id, session_id)
        entry = self._entries.get(key)
        if entry is None:
            return None
        stored_at, payload = entry
        if time.monotonic() - stored_at > self._ttl_seconds:
            self._entries.pop(key, None)
            return None
        return payload

    def set_context(
        self,
        owner_id: str | None,
        session_id: str,
        context: dict[str, Any],
    ) -> None:
        import time

        self._entries[self._key(owner_id, session_id)] = (
            time.monotonic(),
            json.loads(json.dumps(context, default=str)),
        )

    def invalidate(self, owner_id: str | None, session_id: str) -> None:
        self._entries.pop(self._key(owner_id, session_id), None)