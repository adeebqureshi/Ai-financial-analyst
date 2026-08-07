"""
Analysis Router

This module defines the analysis endpoint (``POST /analyze``) which performs
a comprehensive AI-driven financial analysis of a company.

Design Decisions:
    - **No business logic in route**: The route handler delegates entirely
      to ``AnalysisService.analyze()``.
    - **Dependency injection**: ``AnalysisService`` is injected via
      ``Depends(get_analysis_service)``, making it overridable in tests.
    - **Standard response format**: Returns ``APIResponse[AnalyzeResponseData]``
      for consistency with all other endpoints.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_analysis_service
from app.schemas.analysis import AnalyzeRequest
from app.schemas.base import APIResponse
from app.schemas.responses import AnalyzeResponseData
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post(
    "",
    response_model=APIResponse[AnalyzeResponseData],
    summary="Analyze a company",
    description=(
        "Performs a comprehensive AI-driven financial analysis of a company "
        "including valuation, financial health, and an investment recommendation."
    ),
)
async def analyze(
    request: AnalyzeRequest,
    service: AnalysisService = Depends(get_analysis_service),
) -> APIResponse[AnalyzeResponseData]:
    """
    Analyze endpoint.

    Args:
        request: The validated analysis request.
        service: Injected ``AnalysisService`` instance.

    Returns:
        An ``APIResponse`` containing the analysis results.
    """
    result = service.analyze(request)

    return APIResponse.success_response(
        message=f"Analysis completed for {request.ticker}",
        data=result,
    )