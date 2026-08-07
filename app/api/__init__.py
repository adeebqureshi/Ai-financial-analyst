"""
API Package

This package exposes the public API surface for the AI Financial Analyst
application. It re-exports both the legacy non-FastAPI classes (for
backwards compatibility) and the production FastAPI components.

Submodules:
    - ``routers``: FastAPI routers aggregated into ``api_router``.
    - ``middleware``: ASGI middleware (request logging, request ID).
    - ``exceptions``: Global exception handlers.
    - ``dependencies``: FastAPI dependency injection callables.
"""

from __future__ import annotations

# Legacy classes (backwards compatibility)
from .app import FinancialAnalystAPI
from .health import HealthService
from .root import RootService
from .router import AnalysisRouter
from .schemas import AnalyzeRequest, AnalyzeResponse
from .version import VersionService

# Production FastAPI components
from .middleware import RequestLoggingMiddleware
from .routers import api_router
from .exceptions import register_exception_handlers

__all__ = [
    # Legacy
    "FinancialAnalystAPI",
    "AnalysisRouter",
    "AnalyzeRequest",
    "AnalyzeResponse",
    "HealthService",
    "VersionService",
    "RootService",
    # Production
    "RequestLoggingMiddleware",
    "api_router",
    "register_exception_handlers",
]