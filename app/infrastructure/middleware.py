"""
Request middleware.
"""

from __future__ import annotations

import time

from fastapi import Request

from app.infrastructure.request_id import generate_request_id


class RequestMiddleware:

    async def __call__(
        self,
        request: Request,
        call_next,
    ):

        request.state.request_id = generate_request_id()

        start = time.perf_counter()

        response = await call_next(request)

        response.headers["X-Request-ID"] = (
            request.state.request_id
        )

        response.headers["X-Process-Time"] = str(
            time.perf_counter() - start
        )

        return response