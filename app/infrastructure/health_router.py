"""
Health endpoint.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.infrastructure.health import HealthStatus

router = APIRouter()


@router.get("/health")
def health():

    status = HealthStatus()

    return {
        "status": status.status,
        "healthy": status.ok,
        "database": status.database,
        "cache": status.cache,
        "vector_store": status.vector_store,
    }