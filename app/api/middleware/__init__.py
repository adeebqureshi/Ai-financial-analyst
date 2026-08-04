"""
API Middleware Package

This package contains ASGI middleware components for the FastAPI application.

Submodules:
    - ``request_logging``: Logs every HTTP request with method, path,
      status code, and duration.
"""

from __future__ import annotations

from app.api.middleware.request_logging import RequestLoggingMiddleware

__all__ = [
    "RequestLoggingMiddleware",
]