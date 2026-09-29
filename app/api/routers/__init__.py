from __future__ import annotations
from fastapi import APIRouter, Depends
from app.api.routers.analysis import router as analysis_router
from app.api.routers.chat import router as chat_router
from app.api.routers.compare import router as compare_router
from app.api.routers.documents import router as documents_router
from app.api.routers.health import router as health_router
from app.infrastructure.health_router import readiness_router
from app.api.routers.report import router as report_router
from app.api.routers.risk import router as risk_router
from app.api.routers.root import router as root_router
from app.api.routers.search import router as search_router
from app.api.routers.valuation import router as valuation_router
from app.api.routers.version import router as version_router
from app.auth.dependencies import get_current_user
from app.auth.router import router as auth_router
api_router = APIRouter()
_AUTH_GUARD = [Depends(get_current_user)]
api_router.include_router(auth_router)
api_router.include_router(root_router)
api_router.include_router(health_router)
api_router.include_router(readiness_router, tags=["Health"])
api_router.include_router(version_router)
api_router.include_router(analysis_router, dependencies=_AUTH_GUARD)
api_router.include_router(search_router, dependencies=_AUTH_GUARD)
api_router.include_router(valuation_router, dependencies=_AUTH_GUARD)
api_router.include_router(chat_router, dependencies=_AUTH_GUARD)
api_router.include_router(risk_router, dependencies=_AUTH_GUARD)
api_router.include_router(report_router, dependencies=_AUTH_GUARD)
api_router.include_router(compare_router, dependencies=_AUTH_GUARD)
api_router.include_router(documents_router, dependencies=_AUTH_GUARD)
__all__ = [
    "api_router",
    "auth_router",
    "root_router",
    "health_router",
    "version_router",
    "analysis_router",
    "search_router",
    "valuation_router",
    "chat_router",
    "risk_router",
    "report_router",
    "compare_router",
    "documents_router",
]
