"""
Redis cache manager.

Production Decisions:
    - **URL-based configuration**: ``REDIS_URL`` wins when present
      (e.g. ``redis://:password@redis:6379/0``); legacy ``REDIS_HOST`` /
      ``REDIS_PORT`` / ``REDIS_DB`` variables are still honoured so existing
      deployments keep working.
    - **Bounded, socket-timed connections**: The client never hangs the event
      loop or worker thread when Redis is slow or unreachable — connect and
      socket timeouts are enforced (``REDIS_SOCKET_TIMEOUT_SECONDS``).
    - **Health checking**: :meth:`RedisCache.health_check` is a cheap ``PING``
      suitable for readiness probes; :meth:`RedisCache.ping` retains its
      boolean-returning behaviour for backward compatibility.
"""

from __future__ import annotations

import os

import redis


def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default


def build_redis_url() -> str:
    """Resolve the Redis URL from the environment."""
    url = os.getenv("REDIS_URL", "").strip()
    if url:
        return url

    host = os.getenv("REDIS_HOST", "localhost")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PASSWORD", "").strip()

    auth = f":{password}@" if password else ""
    return f"redis://{auth}{host}:{port}/{db}"


class RedisCache:

    def __init__(self) -> None:
        self.url = build_redis_url()

        self.client = redis.Redis.from_url(
            self.url,
            decode_responses=True,
            socket_connect_timeout=_int_env("REDIS_CONNECT_TIMEOUT_SECONDS", 2),
            socket_timeout=_int_env("REDIS_SOCKET_TIMEOUT_SECONDS", 2),
            health_check_interval=30,
        )

    @property
    def host(self) -> str:
        """Connection host (retained for diagnostics/legacy callers)."""
        try:
            return self.client.connection_pool.connection_kwargs.get("host", "localhost")
        except Exception:
            return "localhost"

    @property
    def port(self) -> int:
        """Connection port (retained for diagnostics/legacy callers)."""
        try:
            return int(self.client.connection_pool.connection_kwargs.get("port", 6379))
        except Exception:
            return 6379

    def health_check(self) -> bool:
        """Return True when Redis answers ``PING``."""
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def ping(self) -> bool:
        """Backward-compatible alias for :meth:`health_check`."""
        return self.health_check()

    def close(self) -> None:
        """Release the connection pool."""
        try:
            self.client.close()
        except Exception:
            pass