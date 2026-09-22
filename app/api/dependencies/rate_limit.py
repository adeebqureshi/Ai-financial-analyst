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
    if current_user is not None:
        return f"user:{current_user.id}"
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    return f"ip:{ip}"
def get_anonymous_multiplier(settings: Settings) -> float:
    return settings.rate_limit_anonymous_multiplier
def apply_anonymous_multiplier(
    config: RateLimitConfig,
    multiplier: float,
) -> RateLimitConfig:
    return RateLimitConfig(
        requests_per_minute=max(1, int(config.requests_per_minute * multiplier)),
        requests_per_hour=max(1, int(config.requests_per_hour * multiplier)),
        key_prefix=config.key_prefix,
    )
class RateLimitDependency:
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
        if current_user is None and settings.auth_enabled:
            multiplier = get_anonymous_multiplier(settings)
            config = apply_anonymous_multiplier(config, multiplier)
            identifier = f"anon:{identifier}"
        result = limiter.check_rate_limit(identifier, config)
        if not result.allowed:
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
        request.state.rate_limit_result = result
        return result
rate_limit_chat = RateLimitDependency("chat")
rate_limit_analyze = RateLimitDependency("analyze")
rate_limit_analyze_company = RateLimitDependency("analyze-company")
rate_limit_documents = RateLimitDependency("documents")
rate_limit_search = RateLimitDependency("search")
rate_limit_sandbox = RateLimitDependency("sandbox")
rate_limit_default = RateLimitDependency("default")
def get_rate_limit_dependency(endpoint: str) -> RateLimitDependency:
    return RateLimitDependency(endpoint)
class RateLimitHeadersMiddleware:
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
                message["headers"] = headers
            await send(message)
        await self.app(scope, receive, send_wrapper)
def reset_rate_limits_for_testing() -> None:
    from app.api.rate_limiter import clear_all_rate_limits, reset_rate_limiter
    reset_rate_limiter()
    clear_all_rate_limits()
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