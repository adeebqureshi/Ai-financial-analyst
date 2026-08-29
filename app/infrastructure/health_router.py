"""
Health endpoint.

Reports real infrastructure reachability (database, Redis cache, vector
store). Every probe is independent and failure-tolerant: an unreachable
component reports ``False`` without raising, so monitoring always receives a
structured response.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.health import HealthStatus
from app.infrastructure.startup import startup

router = APIRouter()

_container = None


def _get_container():
    """Lazily create (and cache) the infrastructure container for probing."""
    global _container
    if _container is None:
        _container = startup()
    return _container


def reset_health_container() -> None:
    """Forget the cached probe container (used by tests / worker recycle)."""
    global _container
    _container = None


@router.get("/health")
def health():
    try:
        checks = _get_container().health()
    except Exception:
        checks = {"database": False, "cache": False, "vector_store": False}

    status = HealthStatus(
        status="healthy" if (checks.get("database") and checks.get("vector_store")) else "degraded",
        database=checks.get("database", False),
        cache=checks.get("cache", False),
        vector_store=checks.get("vector_store", False),
    )

    return {
        "status": status.status,
        "healthy": status.ok,
        "database": status.database,
        "cache": status.cache,
        "vector_store": status.vector_store,
        # Cache is reported but deliberately NOT part of ``healthy``: Redis is
        # an optional accelerator with a database fallback in every consumer.
        "cache_optional": True,
    }