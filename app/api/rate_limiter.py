from __future__ import annotations

import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.api.rate_limiter")


def _clock() -> float:
    return time.time()


@dataclass(slots=True)
class RateLimitConfig:

    requests_per_minute: int
    requests_per_hour: int
    key_prefix: str = "ratelimit"


@dataclass(slots=True)
class RateLimitResult:

    allowed: bool
    current_minute: int
    current_hour: int
    limit_minute: int
    limit_hour: int
    retry_after_seconds: int | None = None


class RateLimiterBackend(ABC):

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
        "documents": RateLimitConfig(
            requests_per_minute=settings.rate_limit_documents_per_minute,
            requests_per_hour=settings.rate_limit_documents_per_hour,
            key_prefix="ratelimit:documents",
        ),
        # Uploads parse, chunk, embed and index a PDF, so they get their own
        # bucket. Previously they shared `ratelimit:documents` with the cheap
        # read-only list/delete routes, whose automatic polling exhausted the
        # hourly quota and blocked uploads (429, Retry-After 3600).
        "documents_upload": RateLimitConfig(
            requests_per_minute=settings.rate_limit_documents_per_minute,
            requests_per_hour=settings.rate_limit_documents_per_hour,
            key_prefix="ratelimit:documents:upload",
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

    global _rate_limiter

    with _rate_limiter_lock:
        if _rate_limiter is not None:
            _rate_limiter._local_backend.clear_all()
