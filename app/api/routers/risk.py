"""
Risk Router

This module defines the risk analysis endpoint (``POST /risk-analysis``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_risk_service
from app.schemas.analysis import RiskAnalysisRequest
from app.schemas.base import APIResponse
from app.schemas.responses import RiskAssessmentData
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk-analysis", tags=["Risk"])


@router.post(
    "",
    response_model=APIResponse[RiskAssessmentData],
    summary="Risk analysis",
    description="Assesses financial risk using Piotroski, Altman, and Beneish scores.",
)
async def risk_analysis(
    request: RiskAnalysisRequest,
    service: RiskService = Depends(get_risk_service),
) -> APIResponse[RiskAssessmentData]:
    """
    Risk analysis endpoint.

    Args:
        request: The validated risk analysis request.
        service: Injected ``RiskService`` instance.

    Returns:
        An ``APIResponse`` containing the risk assessment.
    """
    result = service.assess(request)

    return APIResponse.success_response(
        message="Risk assessment completed",
        data=result,
    )