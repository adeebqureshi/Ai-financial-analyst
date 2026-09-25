"""Backward-compatible import surface for the SEC rate limiter.

The canonical SEC rate limiter and the centralized SEC HTTP gateway live in
:mod:`app.data.sec_http`. This module only re-exports them so existing imports
(``from app.data.sec_edgar import SECRateLimiter``) keep working.

There is exactly ONE limiter implementation and ONE Redis key: the names
exported here refer to the very same objects used by the central gateway, so a
legacy caller cannot create a second, competing rate limiter.
"""

from __future__ import annotations

from app.data.sec_http import (
    SEC_MAX_REQUESTS_PER_SECOND,
    SEC_RATE_LIMIT_REDIS_KEY,
    SEC_RATE_LIMIT_WINDOW_SECONDS,
    RedisStrictRateLimiter,
    SECRateLimiter,
    SECRateLimitGrant,
    SECRateLimitUnavailableError,
    get_sec_rate_limiter,
)

__all__ = [
    "RedisStrictRateLimiter",
    "SECRateLimitGrant",
    "SECRateLimitUnavailableError",
    "SECRateLimiter",
    "SEC_MAX_REQUESTS_PER_SECOND",
    "SEC_RATE_LIMIT_REDIS_KEY",
    "SEC_RATE_LIMIT_WINDOW_SECONDS",
    "get_sec_rate_limiter",
]
