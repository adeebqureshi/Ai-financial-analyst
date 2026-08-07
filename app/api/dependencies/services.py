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
    - **Settings injected into services**: Services receive ``Settings``
      as a constructor argument, satisfying the Dependency Inversion
      Principle — services depend on an abstraction (``Settings``),
      not a concrete singleton.
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

from app.core.config import Settings, get_settings
from app.services.health_service import HealthService
from app.services.version_service import VersionService
from app.services.analysis_service import AnalysisService
from app.services.search_service import SearchService
from app.services.company_service import CompanyService
from app.services.valuation_service import ValuationService
from app.services.chat_service import ChatService
from app.services.ratios_service import RatiosService
from app.services.risk_service import RiskService
from app.services.report_service import ReportService
from app.services.compare_service import CompareService
from app.services.screen_service import ScreenService


def get_health_service(
    settings: Settings | None = None,
) -> Iterator[HealthService]:
    """
    FastAPI dependency that yields a ``HealthService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = HealthService(settings)
    yield service


def get_version_service(
    settings: Settings | None = None,
) -> Iterator[VersionService]:
    """
    FastAPI dependency that yields a ``VersionService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = VersionService(settings)
    yield service


def get_analysis_service(
    settings: Settings | None = None,
) -> Iterator[AnalysisService]:
    """
    FastAPI dependency that yields an ``AnalysisService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = AnalysisService(settings)
    yield service


def get_search_service(
    settings: Settings | None = None,
) -> Iterator[SearchService]:
    """
    FastAPI dependency that yields a ``SearchService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = SearchService(settings)
    yield service


def get_company_service(
    settings: Settings | None = None,
) -> Iterator[CompanyService]:
    """
    FastAPI dependency that yields a ``CompanyService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = CompanyService(settings)
    yield service


def get_valuation_service(
    settings: Settings | None = None,
) -> Iterator[ValuationService]:
    """
    FastAPI dependency that yields a ``ValuationService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = ValuationService(settings)
    yield service


def get_chat_service(
    settings: Settings | None = None,
) -> Iterator[ChatService]:
    """
    FastAPI dependency that yields a ``ChatService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = ChatService(settings)
    yield service


def get_ratios_service(
    settings: Settings | None = None,
) -> Iterator[RatiosService]:
    """
    FastAPI dependency that yields a ``RatiosService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = RatiosService(settings)
    yield service


def get_risk_service(
    settings: Settings | None = None,
) -> Iterator[RiskService]:
    """
    FastAPI dependency that yields a ``RiskService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = RiskService(settings)
    yield service


def get_report_service(
    settings: Settings | None = None,
) -> Iterator[ReportService]:
    """
    FastAPI dependency that yields a ``ReportService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = ReportService(settings)
    yield service


def get_compare_service(
    settings: Settings | None = None,
) -> Iterator[CompareService]:
    """
    FastAPI dependency that yields a ``CompareService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = CompareService(settings)
    yield service


def get_screen_service(
    settings: Settings | None = None,
) -> Iterator[ScreenService]:
    """
    FastAPI dependency that yields a ``ScreenService`` instance.
    """
    if settings is None:
        settings = get_settings()
    service = ScreenService(settings)
    yield service
