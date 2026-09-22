from __future__ import annotations
import os
import redis
from app.core.logging import get_logger
logger = get_logger("app.infrastructure.redis")
def _int_env(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        return default
def build_redis_url() -> str:
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
        try:
            return self.client.connection_pool.connection_kwargs.get("host", "localhost")
        except Exception:
            return "localhost"
    @property
    def port(self) -> int:
        try:
            return int(self.client.connection_pool.connection_kwargs.get("port", 6379))
        except Exception:
            return 6379
    def health_check(self) -> bool:
        try:
            return bool(self.client.ping())
        except Exception as exc:
            logger.warning(
                "Redis health check failed: host=%s port=%s error_type=%s error=%s",
                self.host,
                self.port,
                exc.__class__.__name__,
                exc,
            )
            return False
    def ping(self) -> bool:
        return self.health_check()
    def close(self) -> None:
        try:
            self.client.close()
        except Exception:
            pass