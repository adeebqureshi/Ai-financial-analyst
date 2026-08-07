"""
Schemas Package

This package contains all Pydantic v2 request/response schemas (DTOs) for
the AI Financial Analyst API.

Submodules:
    - ``base``:     Standard ``APIResponse[T]`` wrapper, error details, metadata.
    - ``health``:   Health check response schemas.
    - ``version``:  Version info response schemas.
    - ``analysis``: Request models for analysis/valuation/risk/compare/screen endpoints.
    - ``responses``: Response models (DTOs) for all API endpoints.

Typical imports from routers::

    from app.schemas import APIResponse, HealthResponse, VersionResponse
"""

from __future__ import annotations

from app.schemas.base import (
    APIResponse,
    ErrorDetail,
    PaginationMeta,
    ResponseMetadata,
)
from app.schemas.health import ComponentHealth, HealthResponse, HealthStatus
from app.schemas.version import VersionResponse
from app.schemas.analysis import (
    AnalyzeRequest,
    ChatRequest,
    CompareRequest,
    FinancialRatiosRequest,
    FinancialStatementInput,
    IntrinsicValueRequest,
    ReportRequest,
    RiskAnalysisRequest,
    ScreenRequest,
    SearchRequest,
    ValuationParams,
    ValuationRequest,
)
from app.schemas.responses import (
    AnalyzeResponseData,
    ChatResponseData,
    CompanyData,
    CompareItemData,
    CompareResponseData,
    FinancialRatiosData,
    HealthScoreData,
    IntrinsicValueResponseData,
    ReportData,
    RiskAssessmentData,
    ScreenItemData,
    ScreenResponseData,
    SearchHitData,
    SearchResultData,
    ValuationResponseData,
    ValuationResultData,
)

__all__ = [
    # Base
    "APIResponse",
    "ErrorDetail",
    "PaginationMeta",
    "ResponseMetadata",
    # Health
    "ComponentHealth",
    "HealthResponse",
    "HealthStatus",
    # Version
    "VersionResponse",
    # Requests
    "AnalyzeRequest",
    "ChatRequest",
    "CompareRequest",
    "FinancialRatiosRequest",
    "FinancialStatementInput",
    "IntrinsicValueRequest",
    "ReportRequest",
    "RiskAnalysisRequest",
    "ScreenRequest",
    "SearchRequest",
    "ValuationParams",
    "ValuationRequest",
    # Responses
    "AnalyzeResponseData",
    "ChatResponseData",
    "CompanyData",
    "CompareItemData",
    "CompareResponseData",
    "FinancialRatiosData",
    "HealthScoreData",
    "IntrinsicValueResponseData",
    "ReportData",
    "RiskAssessmentData",
    "ScreenItemData",
    "ScreenResponseData",
    "SearchHitData",
    "SearchResultData",
    "ValuationResponseData",
    "ValuationResultData",
]
