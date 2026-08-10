"""
API Routers Package

This package contains all FastAPI routers for the AI Financial Analyst API.
Routers are aggregated into a single ``api_router`` that is included in the
FastAPI application.

Submodules:
    - ``root``:     Root endpoint (``GET /``).
    - ``health``:   Health check endpoint (``GET /health``).
    - ``version``:  Version info endpoint (``GET /version``).
    - ``analysis``: Company analysis endpoint (``POST /analyze``).
    - ``search``:   Semantic search endpoint (``POST /search``).
    - ``company``:  Company profile endpoint (``GET /company/{ticker}``).
    - ``valuation``: Valuation endpoints (``POST /valuation``, ``POST /intrinsic-value``).
    - ``chat``:     Chat endpoint (``POST /chat``).
    - ``ratios``:   Financial ratios endpoint (``POST /financial-ratios``).
    - ``risk``:     Risk analysis endpoint (``POST /risk-analysis``).
    - ``report``:   Report generation endpoint (``POST /report``).
    - ``compare``:  Company comparison endpoint (``POST /compare``).
    - ``screen``:   Stock screening endpoint (``POST /screen``).

Design Decision:
    A single aggregated ``api_router`` is included in ``create_app()``
    rather than including each router individually. This centralizes
    router configuration and makes it easy to add new routers.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routers.analysis import router as analysis_router
from app.api.routers.chat import router as chat_router
from app.api.routers.company import router as company_router
from app.api.routers.compare import router as compare_router
from app.api.routers.documents import router as documents_router
from app.api.routers.health import router as health_router
from app.api.routers.ratios import router as ratios_router
from app.api.routers.report import router as report_router
from app.api.routers.risk import router as risk_router
from app.api.routers.root import router as root_router
from app.api.routers.screen import router as screen_router
from app.api.routers.search import router as search_router
from app.api.routers.valuation import router as valuation_router
from app.api.routers.version import router as version_router

# Aggregated API router — included in the FastAPI app
api_router = APIRouter()

# Include all routers
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(version_router)
api_router.include_router(analysis_router)
api_router.include_router(search_router)
api_router.include_router(company_router)
api_router.include_router(valuation_router)
api_router.include_router(chat_router)
api_router.include_router(ratios_router)
api_router.include_router(risk_router)
api_router.include_router(report_router)
api_router.include_router(compare_router)
api_router.include_router(screen_router)
api_router.include_router(documents_router)

__all__ = [
    "api_router",
    "root_router",
    "health_router",
    "version_router",
    "analysis_router",
    "search_router",
    "company_router",
    "valuation_router",
    "chat_router",
    "ratios_router",
    "risk_router",
    "report_router",
    "compare_router",
    "screen_router",
    "documents_router",
]