from __future__ import annotations
from collections.abc import Iterator
from fastapi import Depends
from app.api.dependencies.settings import get_settings_dep
from app.core.config import Settings
from app.services.analysis_service import AnalysisService
from app.services.chat_service import ChatService
from app.services.compare_service import CompareService
from app.services.document_service import DocumentService
from app.services.health_service import HealthService
from app.services.report_service import ReportService
from app.services.risk_service import RiskService
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
def get_document_service(
    settings: Settings = Depends(get_settings_dep),
) -> Iterator[DocumentService]:
    service = DocumentService(settings)
    yield service
