"""
API Package

This package contains the FastAPI interface layer for the AI Financial
Analyst application. It is the outermost layer in the Clean Architecture
dependency graph.

Subpackages:
    - ``routers``:       FastAPI route handlers (no business logic).
    - ``dependencies``:   Dependency injection callables for settings/services.
    - ``middleware``:     ASGI middleware components.
    - ``exceptions``:     Global exception handlers.

Design Principle:
    The API layer contains no business logic. Routers parse input, call
    services, and format output. All domain logic lives in ``app.services``.
"""

from __future__ import annotations

from app.api.exceptions import register_exception_handlers
from app.api.middleware import RequestLoggingMiddleware
from app.api.routers import api_router

__all__ = [
    "api_router",
    "register_exception_handlers",
    "RequestLoggingMiddleware",
]