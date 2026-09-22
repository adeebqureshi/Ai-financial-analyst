from __future__ import annotations
import time
from typing import Any
from app.core.logging import get_logger
from app.infrastructure.request_id import generate_request_id, set_request_id
logger = get_logger("app.api.middleware")
_REQUEST_ID_HEADER = "x-request-id"
class RequestLoggingMiddleware:
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
        method: str = scope.get("method", "UNKNOWN")
        path: str = scope.get("path", "/")
        query_string: str = scope.get("query_string", b"").decode("utf-8", errors="replace")
        request_id = generate_request_id()
        for name, value in scope.get("headers", []):
            if name == _REQUEST_ID_HEADER.encode("latin-1"):
                incoming = value.decode("latin-1", errors="replace").strip()
                if incoming:
                    request_id = incoming[:128]
                break
        set_request_id(request_id)
        status_code: int = 0
        async def send_wrapper(message: dict[str, Any]) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 0)
                headers = list(message.get("headers", []))
                headers.append(
                    (_REQUEST_ID_HEADER.encode("latin-1"), request_id.encode("latin-1"))
                )
                message = {**message, "headers": headers}
            await send(message)
        start_time = time.perf_counter()
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                "Request failed: %s %s?%s | 500 | %.2fms | request_id=%s",
                method,
                path,
                query_string,
                duration_ms,
                request_id,
            )
            raise
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "Request: %s %s | %d | %.2fms | request_id=%s",
            method,
            path,
            status_code,
            duration_ms,
            request_id,
        )