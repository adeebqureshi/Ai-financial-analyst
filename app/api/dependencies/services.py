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
from app.services.filing_service import FilingService
from app.services.health_service import HealthService
from app.services.market_service import MarketService
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
    service = HealthService(settings)
    yield service
def get_version_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[VersionService]:
    service = VersionService(settings)
    yield service
def get_analysis_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[AnalysisService]:
    service = AnalysisService(settings)
    yield service
def get_search_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[SearchService]:
    service = SearchService(settings)
    yield service
def get_company_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[CompanyService]:
    service = CompanyService(settings)
    yield service
def get_valuation_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ValuationService]:
    service = ValuationService(settings)
    yield service
def get_chat_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ChatService]:
    service = ChatService(settings)
    yield service
def get_ratios_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[RatiosService]:
    service = RatiosService(settings)
    yield service
def get_risk_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[RiskService]:
    service = RiskService(settings)
    yield service
def get_report_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ReportService]:
    service = ReportService(settings)
    yield service
def get_compare_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[CompareService]:
    service = CompareService(settings)
    yield service
def get_screen_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[ScreenService]:
    service = ScreenService(settings)
    yield service
def get_document_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[DocumentService]:
    service = DocumentService(settings)
    yield service
def get_filing_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[FilingService]:
    service = FilingService(settings)
    yield service
def get_market_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[MarketService]:
    service = MarketService(settings)
    yield service