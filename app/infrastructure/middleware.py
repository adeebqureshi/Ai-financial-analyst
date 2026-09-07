"""
Request middleware.

Adds a correlation ID to every request and stamps it into both the request
state and the response headers. The ID is also bound to the logging context
(``app.infrastructure.request_id``) so all log records emitted while the
request is processed carry it.
"""

from __future__ import annotations

import time

from fastapi import Request

from app.infrastructure.request_id import (
    generate_request_id,
    set_request_id,
)


class RequestMiddleware:

    async def __call__(
        self,
        request: Request,
        call_next,
    ):
        # Reuse an incoming X-Request-ID when present (end-to-end tracing);
        # otherwise mint a fresh one. Header values are untrusted input, so
        # the ID is length-capped before use.
        request_id = request.headers.get("X-Request-ID", "").strip()[:128]
        if not request_id:
            request_id = generate_request_id()

        request.state.request_id = request_id
        set_request_id(request_id)

        start = time.perf_counter()

        response = await call_next(request)

        response.headers["X-Request-ID"] = (
            request.state.request_id
        )

        response.headers["X-Process-Time"] = str(
            time.perf_counter() - start
        )

        return response