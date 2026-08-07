"""
Services Package

This package contains the business logic services for the AI Financial
Analyst API. Services encapsulate use-case orchestration and are injected
into routers via FastAPI's dependency injection system.

Submodules:
    - ``health_service``: Application health check logic.
    - ``version_service``: Version info retrieval logic.

Design Principle:
    Routers contain no business logic — they parse input, call a service,
    and format output. All domain logic lives here.
"""

from __future__ import annotations

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

__all__ = [
    "HealthService",
    "VersionService",
    "AnalysisService",
    "SearchService",
    "CompanyService",
    "ValuationService",
    "ChatService",
    "RatiosService",
    "RiskService",
    "ReportService",
    "CompareService",
    "ScreenService",
]
