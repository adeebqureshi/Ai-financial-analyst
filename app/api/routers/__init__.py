"""
API Routers Package

This package contains all FastAPI routers for the AI Financial Analyst API.
Routers are aggregated into a single ``api_router`` that is included in the
FastAPI application.

Submodules:
    - ``root``:    Root endpoint (``GET /``).
    - ``health``:  Health check endpoint (``GET /health``).
    - ``version``: Version info endpoint (``GET /version``).

Design Decision:
    A single aggregated ``api_router`` is included in ``create_app()``
    rather than including each router individually. This centralizes
    router configuration and makes it easy to add new routers.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routers.health import router as health_router
from app.api.routers.root import router as root_router
from app.api.routers.version import router as version_router

# Aggregated API router — included in the FastAPI app
api_router = APIRouter()

# Include all routers
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(version_router)

__all__ = [
    "api_router",
    "root_router",
    "health_router",
    "version_router",
]