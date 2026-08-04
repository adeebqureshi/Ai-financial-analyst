"""
Request Logging Middleware

This module implements an ASGI middleware that logs every incoming HTTP
request and its corresponding response, including method, path, status
code, and duration.

Design Decisions:
    - **Pure ASGI middleware**: Implemented as a pure ASGI middleware class
      (not BaseHTTPMiddleware) for maximum performance. BaseHTTPMiddleware
      wraps each request in a task, adding overhead; pure ASGI passes the
      scope/recv/send directly.
    - **Duration measurement**: Uses ``time.perf_counter()`` for
      high-resolution timing, which is not subject to system clock
      adjustments.
    - **Status code capture**: Intercepts the ``send`` callable to capture
      the response status code from the ``http.response.start`` message.
    - **Structured logging**: Logs are emitted via the core logging
      infrastructure (Rich console + rotating file), ensuring all requests
      are persisted to the log file.
    - **Non-blocking**: Logging is synchronous but fast (no I/O beyond
      the log handler). In production, the log file is on local disk.

Usage:
    The middleware is registered in ``app.main.create_app()``::

        app.add_middleware(RequestLoggingMiddleware)
"""

from __future__ import annotations

import time
from typing import Any

from app.core.logging import get_logger

logger = get_logger("app.api.middleware")


class RequestLoggingMiddleware:
    """
    ASGI middleware for logging HTTP requests and responses.

    This middleware logs the following for each request:
        - HTTP method (GET, POST, etc.)
        - Request path
        - Response status code
        - Duration in milliseconds

    Attributes:
        app: The wrapped ASGI application.
    """

    def __init__(self, app: Any) -> None:
        """
        Initialize the middleware.

        Args:
            app: The ASGI application to wrap.
        """
        self.app = app

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        """
        Process an ASGI request.

        For HTTP requests, this method:
            1. Records the start time.
            2. Wraps the ``send`` callable to capture the status code.
            3. Calls the inner ASGI app.
            4. Logs the request details after completion.

        For non-HTTP requests (e.g., lifespan), it passes through without
        logging.

        Args:
            scope: The ASGI scope dictionary.
            receive: The ASGI receive callable.
            send: The ASGI send callable.
        """
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Extract request info from scope
        method: str = scope.get("method", "UNKNOWN")
        path: str = scope.get("path", "/")
        query_string: str = scope.get("query_string", b"").decode("utf-8", errors="replace")

        # Capture status code from the response
        status_code: int = 0

        async def send_wrapper(message: dict[str, Any]) -> None:
            """Intercept the send callable to capture the status code."""
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
            await send(message)

        # Measure duration
        start_time = time.perf_counter()

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed: %s %s?%s | 500 | %.2fms",
                method,
                path,
                query_string,
                duration_ms,
            )
            raise

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log the request
        logger.info(
            "Request: %s %s | %d | %.2fms",
            method,
            path,
            status_code,
            duration_ms,
        )