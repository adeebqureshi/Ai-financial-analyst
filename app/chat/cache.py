from __future__ import annotations
import json
from typing import TYPE_CHECKING, Any
from app.core.logging import get_logger
if TYPE_CHECKING:
    from redis import Redis
logger = get_logger(__name__)
class ChatSessionCache:
    def __init__(self, redis_url: str, *, ttl_seconds: int = 300) -> None:
        self._redis_url = redis_url
        self._ttl_seconds = ttl_seconds
        self._client: Redis | None = None
        self._healthy = False
    def _connect(self) -> None:
        if self._client is not None:
            return
        try:
            import redis
            client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            client.ping()
            self._client = client
            self._healthy = True
            logger.info("Chat session cache connected to Redis (URL withheld from logs)")
        except Exception:
            self._client = None
            self._healthy = False
    @property
    def enabled(self) -> bool:
        self._connect()
        return self._healthy
    @staticmethod
    def _key(owner_id: str | None, session_id: str) -> str:
        owner = owner_id or "anonymous"
        return f"chat:{owner}:{session_id}:context"
    def get_context(self, owner_id: str | None, session_id: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        try:
            raw = self._client.get(self._key(owner_id, session_id))
            if raw is None:
                return None
            payload = json.loads(raw)
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None
    def set_context(
        self,
        owner_id: str | None,
        session_id: str,
        context: dict[str, Any],
    ) -> None:
        if not self.enabled:
            return
        try:
            self._client.setex(
                self._key(owner_id, session_id),
                self._ttl_seconds,
                json.dumps(context, default=str),
            )
        except Exception:
            return
    def invalidate(self, owner_id: str | None, session_id: str) -> None:
        if not self.enabled:
            return
        try:
            self._client.delete(self._key(owner_id, session_id))
        except Exception:
            return