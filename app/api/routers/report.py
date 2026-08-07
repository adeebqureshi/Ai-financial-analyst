"""
Report Router

This module defines the report generation endpoint (``POST /report``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies.services import get_report_service
from app.schemas.analysis import ReportRequest
from app.schemas.base import APIResponse
from app.schemas.responses import ReportData
from app.services.report_service import ReportService

router = APIRouter(prefix="/report", tags=["Report"])


@router.post(
    "",
    response_model=APIResponse[ReportData],
    summary="Generate a financial report",
    description="Generates a comprehensive LLM-powered financial report for a company.",
)
async def report(
    request: ReportRequest,
    service: ReportService = Depends(get_report_service),
) -> APIResponse[ReportData]:
    """
    Report endpoint.

    Args:
        request: The validated report request.
        service: Injected ``ReportService`` instance.

    Returns:
        An ``APIResponse`` containing the generated report.
    """
    result = service.generate(request)

    return APIResponse.success_response(
        message=f"Report generated for {request.ticker}",
        data=result,
    )