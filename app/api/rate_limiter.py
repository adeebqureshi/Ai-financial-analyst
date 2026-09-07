"""
Rate Limiter Module

Provides production-ready rate limiting with Redis backend and local in-memory fallback.
Supports per-user and per-IP limits with configurable time windows.
"""

from __future__ import annotations

import time
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.api.rate_limiter")


def _clock() -> float:
    """Wall-clock source used to derive rate-limit window keys.

    Returns Unix time in seconds. This indirection exists so tests can
    substitute a frozen/controlled clock for deterministic window
    boundaries. Production semantics are unchanged: the default simply
    returns ``time.time()`` and the sliding-window logic is untouched.
    """
    return time.time()


@dataclass(slots=True)
class RateLimitConfig:
    """Configuration for a specific rate limit rule."""

    requests_per_minute: int
    requests_per_hour: int
    key_prefix: str = "ratelimit"


@dataclass(slots=True)
class RateLimitResult:
    """Result of a rate limit check."""

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
        """Increment counter for key within window, return new count."""

    @abstractmethod
    def get(self, key: str) -> int:
        """Get current count for key."""

    @abstractmethod
    def reset(self, key: str) -> None:
        """Reset counter for key."""

    @abstractmethod
    def health_check(self) -> bool:
        """Check if backend is healthy."""


class LocalMemoryBackend(RateLimiterBackend):
    """Thread-safe in-memory rate limiter backend (fallback when Redis unavailable)."""

    def __init__(self) -> None:
        self._counters: dict[str, tuple[int, float]] = {}
        self._lock = threading.RLock()
        self._cleanup_interval = 300
        self._last_cleanup = time.time()

    def _maybe_cleanup(self) -> None:
        now = time.time()
        if now - self._last_cleanup > self._cleanup_interval:
            expired = [
                k for k, (_, expiry) in self._counters.items() if expiry < now
            ]
            for k in expired:
                del self._counters[k]
            self._last_cleanup = now

    def increment(self, key: str, window_seconds: int) -> int:
        self._maybe_cleanup()
        with self._lock:
            now = time.time()
            expiry = now + window_seconds
            current_count, current_expiry = self._counters.get(key, (0, 0))

            if current_expiry < now:
                current_count = 0

            current_count += 1
            self._counters[key] = (current_count, expiry)
            return current_count

    def get(self, key: str) -> int:
        with self._lock:
            now = time.time()
            current_count, current_expiry = self._counters.get(key, (0, 0))
            if current_expiry < now:
                return 0
            return current_count

    def reset(self, key: str) -> None:
        with self._lock:
            self._counters.pop(key, None)

    def health_check(self) -> bool:
        return True


class RedisBackend(RateLimiterBackend):
    """
    Redis-backed rate limiter for distributed deployments.

    The client is created lazily and re-created after failures, so a Redis
    restart or network blip is healed on the next request instead of pinning
    the limiter to a dead connection.
    """

    # Minimum seconds between reconnect attempts (avoid hammering a down Redis).
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
            logger.info("Rate limiter connected to Redis (URL withheld from logs)")
        except Exception as exc:
            logger.warning("Failed to connect to Redis for rate limiting: %s. Using local fallback.", exc)
            self._client = None

    def _ensure_client(self) -> Any:
        if self._client is None and self._cooldown_elapsed():
            self._connect()
        return self._client

    def _cooldown_elapsed(self) -> bool:
        return (time.monotonic() - self._last_connect_attempt) >= self._reconnect_cooldown_seconds

    def _drop_client(self) -> None:
        """Forget the current client so the next call reconnects (heals restarts)."""
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
            return results[0]
        except Exception as exc:
            logger.warning("Redis increment failed, falling back to local: %s", exc)
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
            return client.ping()
        except Exception:
            return False


class HybridRateLimiter:
    """
    Rate limiter with Redis backend and automatic local fallback.

    Uses Redis when available for distributed rate limiting across multiple
    application instances. Automatically falls back to thread-safe in-memory
    storage when Redis is unavailable.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._redis_backend = RedisBackend(self._settings.rate_limit_redis_url)
        self._local_backend = LocalMemoryBackend()
        self._use_redis = self._redis_backend.health_check()
        self._backend: RateLimiterBackend = (
            self._redis_backend if self._use_redis else self._local_backend
        )
        self._last_redis_probe = time.monotonic()

        logger.info(
            "Rate limiter initialized with %s backend",
            "Redis" if self._use_redis else "local memory",
        )

    # How often (seconds) a locally-fallen-back limiter re-probes Redis so a
    # recovered Redis instance takes over again without a process restart.
    _redis_reprobe_interval_seconds = 30.0

    def _get_backend(self) -> RateLimiterBackend:
        if self._use_redis:
            if not self._redis_backend.health_check():
                logger.warning("Redis health check failed, switching to local backend")
                self._use_redis = False
                self._backend = self._local_backend
                self._last_redis_probe = time.monotonic()
            return self._backend

        # Currently on the local backend: periodically probe Redis so a
        # recovered instance is adopted again (multi-instance consistency).
        now = time.monotonic()
        if (
            now - self._last_redis_probe >= self._redis_reprobe_interval_seconds
            and self._redis_backend.health_check()
        ):
            logger.info("Redis recovered, switching rate limiter back to Redis backend")
            self._use_redis = True
            self._backend = self._redis_backend
        self._last_redis_probe = now
        return self._backend

    def check_rate_limit(
        self,
        identifier: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """
        Check if request is within rate limits.

        Args:
            identifier: Unique identifier (user ID or IP address)
            config: Rate limit configuration for this endpoint

        Returns:
            RateLimitResult with allowance decision and current counts
        """
        if not self._settings.rate_limit_enabled:
            return RateLimitResult(
                allowed=True,
                current_minute=0,
                current_hour=0,
                limit_minute=config.requests_per_minute,
                limit_hour=config.requests_per_hour,
            )

        backend = self._get_backend()

        minute_key = f"{config.key_prefix}:{identifier}:minute:{int(_clock() // 60)}"
        hour_key = f"{config.key_prefix}:{identifier}:hour:{int(_clock() // 3600)}"

        try:
            current_minute = backend.increment(minute_key, 60)
            current_hour = backend.increment(hour_key, 3600)
        except Exception:
            backend = self._local_backend
            current_minute = backend.increment(minute_key, 60)
            current_hour = backend.increment(hour_key, 3600)

        allowed = (
            current_minute <= config.requests_per_minute
            and current_hour <= config.requests_per_hour
        )

        retry_after = None
        if not allowed:
            if current_minute > config.requests_per_minute:
                retry_after = 60 - (int(_clock()) % 60)
            else:
                retry_after = 3600 - (int(_clock()) % 3600)

        return RateLimitResult(
            allowed=allowed,
            current_minute=current_minute,
            current_hour=current_hour,
            limit_minute=config.requests_per_minute,
            limit_hour=config.requests_per_hour,
            retry_after_seconds=retry_after,
        )

    def reset_limits(self, identifier: str, prefix: str = "ratelimit") -> None:
        """Reset all rate limits for an identifier (admin operation)."""
        backend = self._get_backend()
        minute_key = f"{prefix}:{identifier}:minute:{int(_clock() // 60)}"
        hour_key = f"{prefix}:{identifier}:hour:{int(_clock() // 3600)}"
        backend.reset(minute_key)
        backend.reset(hour_key)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint-specific configurations
# ──────────────────────────────────────────────────────────────────────────────

def get_endpoint_config(endpoint: str, settings: Settings) -> RateLimitConfig:
    """Get rate limit configuration for a specific endpoint."""
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


# ──────────────────────────────────────────────────────────────────────────────
# Singleton access
# ──────────────────────────────────────────────────────────────────────────────

_rate_limiter: HybridRateLimiter | None = None
_rate_limiter_lock = threading.Lock()


def get_rate_limiter(settings: Settings | None = None) -> HybridRateLimiter:
    """Get or create the singleton rate limiter instance."""
    global _rate_limiter
    with _rate_limiter_lock:
        if _rate_limiter is None:
            _rate_limiter = HybridRateLimiter(settings)
        return _rate_limiter


def reset_rate_limiter() -> None:
    """Reset the singleton (for testing)."""
    global _rate_limiter
    with _rate_limiter_lock:
        _rate_limiter = None