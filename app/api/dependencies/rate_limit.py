"""
Rate Limiting Dependencies

FastAPI dependency callables for enforcing rate limits on endpoints.
Supports per-user (authenticated) and per-IP (anonymous) limits.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status
from fastapi.security.utils import get_authorization_scheme_param

from app.api.rate_limiter import (
    HybridRateLimiter,
    RateLimitConfig,
    RateLimitResult,
    get_endpoint_config,
    get_rate_limiter,
    reset_rate_limiter,
)
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger("app.api.rate_limit")

if TYPE_CHECKING:
    from app.core.config import Settings


def get_client_identifier(
    request: Request,
    current_user: User | None,
    settings: Settings,
) -> str:
    """
    Get the rate limit identifier for the current request.

    For authenticated users, uses the user ID.
    For anonymous requests, uses the client IP address.
    """
    if current_user is not None:
        return f"user:{current_user.id}"

    # Anonymous: use IP address
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"

    return f"ip:{ip}"


def get_anonymous_multiplier(settings: Settings) -> float:
    """Get the rate limit multiplier for anonymous requests."""
    return settings.rate_limit_anonymous_multiplier


def apply_anonymous_multiplier(
    config: RateLimitConfig,
    multiplier: float,
) -> RateLimitConfig:
    """Apply anonymous multiplier to rate limit config."""
    return RateLimitConfig(
        requests_per_minute=max(1, int(config.requests_per_minute * multiplier)),
        requests_per_hour=max(1, int(config.requests_per_hour * multiplier)),
        key_prefix=config.key_prefix,
    )


class RateLimitDependency:
    """
    FastAPI dependency for rate limiting a specific endpoint.

    Usage:
        rate_limit_chat = RateLimitDependency("chat")

        @router.post("/chat", dependencies=[Depends(rate_limit_chat)])
        async def chat(...):
            ...
    """

    def __init__(self, endpoint: str) -> None:
        self.endpoint = endpoint

    def __call__(
        self,
        request: Request,
        current_user: User | None = Depends(get_current_user),
        settings: Settings = Depends(get_settings),
    ) -> RateLimitResult:
        limiter = get_rate_limiter(settings)
        config = get_endpoint_config(self.endpoint, settings)

        identifier = get_client_identifier(request, current_user, settings)

        # Apply stricter limits for anonymous users
        if current_user is None and settings.auth_enabled:
            multiplier = get_anonymous_multiplier(settings)
            config = apply_anonymous_multiplier(config, multiplier)
            identifier = f"anon:{identifier}"

        result = limiter.check_rate_limit(identifier, config)

        if not result.allowed:
            # Security-relevant signal, logged without any credentials or
            # request content — identifier is a user ID or client IP only.
            logger.warning(
                "Rate limit exceeded: endpoint=%s identifier=%s minute=%s/%s hour=%s/%s retry_after=%ss",
                self.endpoint,
                identifier,
                result.current_minute,
                result.limit_minute,
                result.current_hour,
                result.limit_hour,
                result.retry_after_seconds,
            )
            headers = {}
            if result.retry_after_seconds is not None:
                headers["Retry-After"] = str(result.retry_after_seconds)
            headers["X-RateLimit-Limit-Minute"] = str(result.limit_minute)
            headers["X-RateLimit-Remaining-Minute"] = str(
                max(0, result.limit_minute - result.current_minute)
            )
            headers["X-RateLimit-Limit-Hour"] = str(result.limit_hour)
            headers["X-RateLimit-Remaining-Hour"] = str(
                max(0, result.limit_hour - result.current_hour)
            )

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {self.endpoint}. Try again in {result.retry_after_seconds} seconds.",
                headers=headers,
            )

        # Add rate limit headers to successful responses
        request.state.rate_limit_result = result

        return result


# ──────────────────────────────────────────────────────────────────────────────
# Pre-configured dependencies for each endpoint
# ──────────────────────────────────────────────────────────────────────────────

rate_limit_chat = RateLimitDependency("chat")
rate_limit_analyze = RateLimitDependency("analyze")
rate_limit_analyze_company = RateLimitDependency("analyze-company")
rate_limit_documents = RateLimitDependency("documents")
rate_limit_search = RateLimitDependency("search")
rate_limit_sandbox = RateLimitDependency("sandbox")
rate_limit_default = RateLimitDependency("default")


def get_rate_limit_dependency(endpoint: str) -> RateLimitDependency:
    """Factory function to get rate limit dependency for an endpoint."""
    return RateLimitDependency(endpoint)


# ──────────────────────────────────────────────────────────────────────────────
# Middleware for adding rate limit headers to all responses
# ──────────────────────────────────────────────────────────────────────────────

class RateLimitHeadersMiddleware:
    """
    ASGI middleware to add rate limit headers to all responses.

    This middleware reads the rate limit result from request.state
    (set by the rate limit dependency) and adds appropriate headers.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message: dict[str, Any]) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                # Rate limit headers would be added by the dependency
                # This is a placeholder for any global headers
                message["headers"] = headers
            await send(message)

        await self.app(scope, receive, send_wrapper)


# ──────────────────────────────────────────────────────────────────────────────
# Testing utilities
# ──────────────────────────────────────────────────────────────────────────────

def reset_rate_limits_for_testing() -> None:
    """Reset rate limiter state for testing."""
    reset_rate_limiter()


__all__ = [
    "RateLimitDependency",
    "rate_limit_chat",
    "rate_limit_analyze",
    "rate_limit_analyze_company",
    "rate_limit_documents",
    "rate_limit_search",
    "rate_limit_sandbox",
    "rate_limit_default",
    "get_rate_limit_dependency",
    "RateLimitHeadersMiddleware",
    "reset_rate_limits_for_testing",
    "get_client_identifier",
    "apply_anonymous_multiplier",
]