"""
Service Dependency Injection

This module provides FastAPI dependency callables for injecting service
instances into route handlers. Each service is constructed with the
application ``Settings`` and yielded for the duration of the request.

Design Decisions:
    - **Factory functions, not globals**: Services are instantiated
      per-request via dependency factories. This ensures clean state
      between requests and makes services mockable in tests via
      ``app.dependency_overrides``.
    - **Settings injected via ``Depends``**: Settings are resolved through
      ``get_settings_dep`` instead of an optional ``settings`` parameter.
      If ``settings`` were a plain parameter FastAPI would treat it as a
      request body field, forcing clients to nest the real payload under a
      ``request`` key (``{"request": {...}, "settings": {...}}``) and
      causing HTTP 422 validation failures on every endpoint.
    - **Yield-based**: Using ``yield`` allows cleanup logic (if needed)
      after the request completes.

Usage in a route::

    from fastapi import Depends
    from app.api.dependencies.services import get_health_service
    from app.services.health_service import HealthService

    @router.get("/health")
    async def health(service: HealthService = Depends(get_health_service)):
        return service.check_health()
"""

from __future__ import annotations

from collections.abc import Iterator

from fastapi import Depends

from app.api.dependencies.settings import get_settings_dep
from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.chat_service import ChatService
from app.services.compare_service import CompareService
from app.services.company_service import CompanyService
from app.services.document_service import DocumentService
from app.services.health_service import HealthService
from app.services.ratios_service import RatiosService
from app.services.report_service import ReportService
from app.services.risk_service import RiskService
from app.services.screen_service import ScreenService
from app.services.search_service import SearchService
from app.services.valuation_service import ValuationService
from app.services.version_service import VersionService


def get_health_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[HealthService]:
    """
    FastAPI dependency that yields a ``HealthService`` instance.
    """
    service = HealthService(settings)
    yield service


def get_version_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[VersionService]:
    """
    FastAPI dependency that yields a ``VersionService`` instance.
    """
    service = VersionService(settings)
    yield service


def get_analysis_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[AnalysisService]:
    """
    FastAPI dependency that yields an ``AnalysisService`` instance.
    """
    service = AnalysisService(settings)
    yield service


def get_search_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[SearchService]:
    """
    FastAPI dependency that yields a ``SearchService`` instance.
    """
    service = SearchService(settings)
    yield service


def get_company_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[CompanyService]:
    """
    FastAPI dependency that yields a ``CompanyService`` instance.
    """
    service = CompanyService(settings)
    yield service


def get_valuation_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ValuationService]:
    """
    FastAPI dependency that yields a ``ValuationService`` instance.
    """
    service = ValuationService(settings)
    yield service


def get_chat_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ChatService]:
    """
    FastAPI dependency that yields a ``ChatService`` instance.
    """
    service = ChatService(settings)
    yield service


def get_ratios_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[RatiosService]:
    """
    FastAPI dependency that yields a ``RatiosService`` instance.
    """
    service = RatiosService(settings)
    yield service


def get_risk_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[RiskService]:
    """
    FastAPI dependency that yields a ``RiskService`` instance.
    """
    service = RiskService(settings)
    yield service


def get_report_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ReportService]:
    """
    FastAPI dependency that yields a ``ReportService`` instance.
    """
    service = ReportService(settings)
    yield service


def get_compare_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[CompareService]:
    """
    FastAPI dependency that yields a ``CompareService`` instance.
    """
    service = CompareService(settings)
    yield service


def get_screen_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ScreenService]:
    """
    FastAPI dependency that yields a ``ScreenService`` instance.
    """
    service = ScreenService(settings)
    yield service


def get_document_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[DocumentService]:
    """
    FastAPI dependency that yields a ``DocumentService`` instance.
    """
    service = DocumentService(settings)
    yield service
