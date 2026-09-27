from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

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

    @abstractmethod
    def clear_all(self) -> None:
        raise NotImplementedError


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


class HybridRateLimiter:
    """Rate limiter backed by an in-process counter.

    The project runs a single backend worker, so request counters live in a
    thread-safe in-process map. This replaces the previous Redis-backed
    implementation: a distributed counter is unnecessary at this scale, and the
    local backend was already the automatic fallback whenever Redis was
    unreachable, so behaviour is unchanged for the local/demo setup.

    The class name is retained for API compatibility with existing callers.
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()

        self._local_backend = LocalMemoryBackend()

        self._backend: RateLimiterBackend = self._local_backend

        logger.info("Rate limiter initialized with in-process backend")

    def _get_backend(self) -> RateLimiterBackend:
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
                # A denial on the hourly bucket must advertise an hour-scale
                # retry interval, not the remaining seconds in the current
                # hour. This also avoids a misleading near-boundary value.
                retry_after = 3600

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
            except Exception:
                pass

        _rate_limiter = None
        _rate_limiter_settings = None


def clear_all_rate_limits() -> None:
    """Clear all in-process rate-limit counters."""

    global _rate_limiter

    with _rate_limiter_lock:
        if _rate_limiter is not None:
            _rate_limiter._local_backend.clear_all()