from __future__ import annotations

import json
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)


class ChatSessionCache:

    def __init__(self, redis_url: str = "", *, ttl_seconds: int = 300) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[str, tuple[float, dict[str, Any]]] = {}

    @property
    def enabled(self) -> bool:
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
