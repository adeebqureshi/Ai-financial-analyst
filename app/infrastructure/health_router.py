from __future__ import annotations
import time
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.logging import get_logger
from app.infrastructure.startup import startup
readiness_router = APIRouter()
logger = get_logger("app.infrastructure.health_router")
_container = None
def _get_container():
    global _container
    if _container is None:
        _container = startup()
    return _container
def reset_health_container() -> None:
    global _container
    _container = None
@readiness_router.get("/readiness")
def readiness():
    start = time.perf_counter()
    try:
        checks = _get_container().health()
    except Exception as exc:
        logger.warning(
            "Readiness probe failed: error_type=%s error=%s",
            exc.__class__.__name__,
            exc,
        )
        checks = {"database": False, "cache": False, "vector_store": False}
    ok = checks.get("database", False) and checks.get("vector_store", False)
    duration_ms = (time.perf_counter() - start) * 1000
    if not ok:
        logger.warning(
            "Readiness check failed: database=%s vector_store=%s duration_ms=%.1f",
            checks.get("database", False),
            checks.get("vector_store", False),
            duration_ms,
        )
    return JSONResponse(
        status_code=status.HTTP_200_OK if ok else status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "status": "ready" if ok else "not_ready",
            "ready": ok,
            "database": checks.get("database", False),
            "vector_store": checks.get("vector_store", False),
            "cache": checks.get("cache", False),
            "cache_optional": True,
            "duration_ms": round(duration_ms, 1),
        },
    )
