"""
API Package

This package exposes the public API surface for the AI Financial Analyst
application.

Submodules:
    - ``routers``: FastAPI routers aggregated into ``api_router``.
    - ``middleware``: ASGI middleware (request logging, request ID).
    - ``exceptions``: Global exception handlers.
    - ``dependencies``: FastAPI dependency injection callables.
"""

from __future__ import annotations

# Production FastAPI components
from app.api.router import AnalysisRouter
from app.api.schemas import AnalyzeRequest

from .middleware import RequestLoggingMiddleware
from .routers import api_router
from .exceptions import register_exception_handlers


class FinancialAnalystAPI:
    """
    Thin programmatic facade over the legacy analysis router.

    Provided for backward compatibility with earlier integrations and tests.
    New callers should use the FastAPI application from ``app.main``.
    """

    def __init__(self) -> None:
        self.router = AnalysisRouter()

    def analyze(
        self,
        ticker: str,
        query: str,
        result: dict,
        context: str,
    ):
        request = AnalyzeRequest(
            ticker=ticker,
            query=query,
        )

        return self.router.analyze(
            request=request,
            result=result,
            context=context,
        )


__all__ = [
    "RequestLoggingMiddleware",
    "api_router",
    "register_exception_handlers",
    "FinancialAnalystAPI",
    "AnalysisRouter",
    "AnalyzeRequest",
]