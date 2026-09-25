from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.api.rate_limiter")


def _clock() -> float:
    """Return the current Unix timestamp."""
    return time.time()


@dataclass(slots=True)
class RateLimitConfig:
    """Configuration for a specific rate-limit rule."""

    requests_per_minute: int
    requests_per_hour: int
    key_prefix: str = "ratelimit"


@dataclass(slots=True)
class RateLimitResult:
    """Result of a rate-limit check."""

    allowed: bool
    current_minute: int
    current_hour: int
    limit_minute: int
    limit_hour: int
    retry_after_seconds: int | None = None


class RateLimiterBackend(ABC):
    """Abstract base class for rate limiter backends."""

    @abstractmethod
    def increment(self, key: str, window_seconds: int) -> int:
        raise NotImplementedError

    @abstractmethod
    def get(self, key: str) -> int:
        raise NotImplementedError

    @abstractmethod
    def reset(self, key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> bool:
        raise NotImplementedError

    def clear_all(self) -> None:
        pass


class LocalMemoryBackend(RateLimiterBackend):
    """Thread-safe in-memory rate limiter backend."""

    def __init__(self) -> None:
        self._counters: dict[str, tuple[int, float]] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 300
        self._last_cleanup = time.time()

    def _maybe_cleanup(self) -> None:
        now = time.time()

        if now - self._last_cleanup > self._cleanup_interval:
            with self._lock:
                expired = [
                    key
                    for key, (_, expiry) in self._counters.items()
                    if expiry < now
                ]

                for key in expired:
                    del self._counters[key]

                self._last_cleanup = now

    def increment(self, key: str, window_seconds: int) -> int:
        self._maybe_cleanup()

        with self._lock:
            now = time.time()
            expiry = now + window_seconds

            current_count, current_expiry = self._counters.get(
                key,
                (0, 0),
            )

            if current_expiry < now:
                current_count = 0

            current_count += 1
            self._counters[key] = (current_count, expiry)

            return current_count

    def get(self, key: str) -> int:
        with self._lock:
            now = time.time()

            current_count, current_expiry = self._counters.get(
                key,
                (0, 0),
            )

            if current_expiry < now:
                return 0

            return current_count

    def reset(self, key: str) -> None:
        with self._lock:
            self._counters.pop(key, None)

    def health_check(self) -> bool:
        return True

    def clear_all(self) -> None:
        with self._lock:
            self._counters.clear()


class RedisBackend(RateLimiterBackend):
    """Redis-backed rate limiter backend."""

    _reconnect_cooldown_seconds = 5.0

    def __init__(self, redis_url: str) -> None:
        self._redis_url = redis_url
        self._client: Any = None
        self._last_connect_attempt = 0.0

        self._connect()

    def _connect(self) -> None:
        self._last_connect_attempt = time.monotonic()

        try:
            import redis

            self._client = redis.from_url(
                self._redis_url,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
                health_check_interval=30,
            )

            self._client.ping()

            logger.info(
                "Rate limiter connected to Redis (URL withheld from logs)"
            )

        except Exception as exc:
            logger.warning(
                "Failed to connect to Redis for rate limiting: %s. "
                "Using local fallback.",
                exc,
            )
            self._client = None

    def _ensure_client(self) -> Any:
        if self._client is None and self._cooldown_elapsed():
            self._connect()

        return self._client

    def _cooldown_elapsed(self) -> bool:
        return (
            time.monotonic() - self._last_connect_attempt
            >= self._reconnect_cooldown_seconds
        )

    def _drop_client(self) -> None:
        self._client = None

    def increment(self, key: str, window_seconds: int) -> int:
        client = self._ensure_client()

        if client is None:
            raise RuntimeError("Redis client not available")

        try:
            pipe = client.pipeline()

            pipe.incr(key)
            pipe.expire(key, window_seconds)

            results = pipe.execute()

            return int(results[0])

        except Exception as exc:
            logger.warning(
                "Redis increment failed, falling back to local: %s",
                exc,
            )

            self._drop_client()
            raise

    def get(self, key: str) -> int:
        client = self._ensure_client()

        if client is None:
            raise RuntimeError("Redis client not available")

        try:
            value = client.get(key)

            return int(value) if value else 0

        except Exception as exc:
            logger.warning("Redis get failed: %s", exc)

            self._drop_client()
            raise

    def reset(self, key: str) -> None:
        client = self._ensure_client()

        if client is None:
            raise RuntimeError("Redis client not available")

        try:
            client.delete(key)

        except Exception as exc:
            logger.warning("Redis reset failed: %s", exc)

            self._drop_client()
            raise

    def health_check(self) -> bool:
        client = self._ensure_client()

        if client is None:
            return False

        try:
            return bool(client.ping())

        except Exception:
            return False

    def clear_all(self) -> None:
        client = self._ensure_client()

        if client is None:
            return

        try:
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = client.scan(
                    cursor,
                    match="ratelimit:*",
                    count=100,
                )

                if keys:
                    client.delete(*keys)
                    deleted_count += len(keys)

                if cursor == 0:
                    break

            if deleted_count:
                logger.info(
                    "Cleared %d rate limit keys from Redis for testing",
                    deleted_count,
                )

        except Exception as exc:
            logger.warning(
                "Failed to clear Redis rate limit keys: %s",
                exc,
            )

            self._drop_client()
            raise


class HybridRateLimiter:
    """Rate limiter with Redis backend and local fallback."""

    _redis_reprobe_interval_seconds = 30.0

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

        self._redis_backend = RedisBackend(
            self._settings.rate_limit_redis_url
        )

        self._local_backend = LocalMemoryBackend()

        self._use_redis = self._redis_backend.health_check()

        self._backend: RateLimiterBackend = (
            self._redis_backend
            if self._use_redis
            else self._local_backend
        )

        self._last_redis_probe = time.monotonic()

        logger.info(
            "Rate limiter initialized with %s backend",
            "Redis" if self._use_redis else "local memory",
        )

    def _get_backend(self) -> RateLimiterBackend:
        if self._use_redis:
            if not self._redis_backend.health_check():
                logger.warning(
                    "Redis health check failed, switching to local backend"
                )

                self._use_redis = False
                self._backend = self._local_backend
                self._last_redis_probe = time.monotonic()

            return self._backend

        now = time.monotonic()

        if (
            now - self._last_redis_probe
            >= self._redis_reprobe_interval_seconds
            and self._redis_backend.health_check()
        ):
            logger.info(
                "Redis recovered, switching rate limiter back to Redis backend"
            )

            self._use_redis = True
            self._backend = self._redis_backend

        self._last_redis_probe = now

        return self._backend

    def check_rate_limit(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check whether a request is within the configured limits."""

        if not self._settings.rate_limit_enabled:
            return RateLimitResult(
                allowed=True,
                current_minute=0,
                current_hour=0,
                limit_minute=config.requests_per_minute,
                limit_hour=config.requests_per_hour,
            )

        backend = self._get_backend()
        current_time = _clock()

        minute_key = (
            f"{config.key_prefix}:"
            f"{identifier}:minute:{int(current_time // 60)}"
        )

        hour_key = (
            f"{config.key_prefix}:"
            f"{identifier}:hour:{int(current_time // 3600)}"
        )

        try:
            current_minute = backend.increment(
                minute_key,
                60,
            )

            current_hour = backend.increment(
                hour_key,
                3600,
            )

        except Exception:
            backend = self._local_backend

            current_minute = backend.increment(
                minute_key,
                60,
            )

            current_hour = backend.increment(
                hour_key,
                3600,
            )

        allowed = (
            current_minute <= config.requests_per_minute
            and current_hour <= config.requests_per_hour
        )

        retry_after = None

        if not allowed:
            if current_minute > config.requests_per_minute:
                retry_after = 60 - (int(current_time) % 60)
            else:
                retry_after = 3600 - (int(current_time) % 3600)

        return RateLimitResult(
            allowed=allowed,
            current_minute=current_minute,
            current_hour=current_hour,
            limit_minute=config.requests_per_minute,
            limit_hour=config.requests_per_hour,
            retry_after_seconds=retry_after,
        )

    def reset_limits(
        self,
        identifier: str,
        prefix: str = "ratelimit",
    ) -> None:
        """Reset the current minute/hour limits for an identifier."""

        backend = self._get_backend()
        current_time = _clock()

        minute_key = (
            f"{prefix}:"
            f"{identifier}:minute:{int(current_time // 60)}"
        )

        hour_key = (
            f"{prefix}:"
            f"{identifier}:hour:{int(current_time // 3600)}"
        )

        backend.reset(minute_key)
        backend.reset(hour_key)


def get_endpoint_config(
    endpoint: str,
    settings: Settings,
) -> RateLimitConfig:
    """Get the rate-limit configuration for an endpoint."""

    configs = {
        "chat": RateLimitConfig(
            requests_per_minute=settings.rate_limit_chat_per_minute,
            requests_per_hour=settings.rate_limit_chat_per_hour,
            key_prefix="ratelimit:chat",
        ),
        "analyze": RateLimitConfig(
            requests_per_minute=settings.rate_limit_analyze_per_minute,
            requests_per_hour=settings.rate_limit_analyze_per_hour,
            key_prefix="ratelimit:analyze",
        ),
        "analyze-company": RateLimitConfig(
            requests_per_minute=settings.rate_limit_analyze_per_minute,
            requests_per_hour=settings.rate_limit_analyze_per_hour,
            key_prefix="ratelimit:analyze",
        ),
        "documents": RateLimitConfig(
            requests_per_minute=settings.rate_limit_documents_per_minute,
            requests_per_hour=settings.rate_limit_documents_per_hour,
            key_prefix="ratelimit:documents",
        ),
        "search": RateLimitConfig(
            requests_per_minute=settings.rate_limit_search_per_minute,
            requests_per_hour=settings.rate_limit_search_per_hour,
            key_prefix="ratelimit:search",
        ),
        "sandbox": RateLimitConfig(
            requests_per_minute=settings.rate_limit_sandbox_per_minute,
            requests_per_hour=settings.rate_limit_sandbox_per_hour,
            key_prefix="ratelimit:sandbox",
        ),
        "default": RateLimitConfig(
            requests_per_minute=settings.rate_limit_default_per_minute,
            requests_per_hour=settings.rate_limit_default_per_hour,
            key_prefix="ratelimit:default",
        ),
    }

    return configs.get(endpoint, configs["default"])


_rate_limiter: HybridRateLimiter | None = None
_rate_limiter_settings: Settings | None = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter(
    settings: Settings | None = None,
) -> HybridRateLimiter:
    """
    Return the singleton rate limiter.

    Recreate the singleton when a different Settings instance is supplied.
    This is important for tests and dependency overrides that provide
    temporary rate-limit configuration.
    """

    global _rate_limiter
    global _rate_limiter_settings

    resolved_settings = settings or get_settings()

    with _rate_limiter_lock:
        if (
            _rate_limiter is None
            or _rate_limiter_settings is not resolved_settings
        ):
            _rate_limiter = HybridRateLimiter(resolved_settings)
            _rate_limiter_settings = resolved_settings

        return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the singleton rate limiter and clear its state."""

    global _rate_limiter
    global _rate_limiter_settings

    with _rate_limiter_lock:
        if _rate_limiter is not None:
            try:
                _rate_limiter._local_backend.clear_all()
                _rate_limiter._redis_backend.clear_all()
            except Exception:
                pass

        _rate_limiter = None
        _rate_limiter_settings = None


def clear_all_rate_limits() -> None:
    """Clear all Redis and local rate-limit counters."""

    settings = get_settings()

    redis_backend = RedisBackend(
        settings.rate_limit_redis_url
    )

    redis_backend.clear_all()

    global _rate_limiter

    with _rate_limiter_lock:
        if _rate_limiter is not None:
            _rate_limiter._local_backend.clear_all()