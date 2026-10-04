from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.pdf_report_service import (
    AnalysisPdfPayload,
    PdfReportError,
    build_filename,
    render_analysis_pdf,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/analysis", tags=["Analysis"])


class AnalysisPdfRequest(BaseModel):
    """
    The analysis result the workspace has already computed.

    This endpoint is a renderer, not an analyser: it accepts the payload the
    client is already displaying so producing the PDF never re-runs market
    data, the valuation model, the health scores or the LLM.
    """

    ticker: str = Field(..., min_length=1, max_length=16)
    company: dict[str, Any] = Field(...)
    market: dict[str, Any] = Field(default_factory=dict)
    statement: dict[str, Any] = Field(default_factory=dict)
    valuation: dict[str, Any] = Field(default_factory=dict)
    health: dict[str, Any] = Field(default_factory=dict)
    recommendation: str = Field(default="")
    risk: dict[str, Any] | None = Field(default=None)


@router.post(
    "/pdf-report",
    summary="Download a completed analysis as a PDF report",
    description=(
        "Renders the supplied analysis result as a professional PDF. No "
        "analysis, valuation or language-model work is performed -- the "
        "document reflects exactly the numbers supplied."
    ),
    response_class=Response,
    responses={
        200: {
            "content": {"application/pdf": {}},
            "description": "The rendered PDF report.",
        }
    },
)
async def analysis_pdf_report(payload: AnalysisPdfRequest) -> Response:
    if not payload.company:
        raise HTTPException(
            status_code=422,
            detail="Company data is required to build a report.",
        )

    ticker = payload.ticker.strip()

    try:
        document = render_analysis_pdf(
            AnalysisPdfPayload(
                ticker=ticker,
                company=payload.company,
                market=payload.market,
                statement=payload.statement,
                valuation=payload.valuation,
                health=payload.health,
                recommendation=payload.recommendation,
                risk=payload.risk,
            )
        )
    except PdfReportError as exc:
        logger.warning("Analysis PDF rendering failed for %s: %s", ticker, exc)
        raise HTTPException(
            status_code=500,
            detail="Unable to generate the report. Please try again.",
        ) from exc

    filename = build_filename(ticker)

    return Response(
        content=document,
        media_type="application/pdf",
        headers={
            # `filename` keeps non-ASCII tickers safe; `filename*` carries the
            # RFC 5987 form for full Unicode fidelity.
            "Content-Disposition": (
                f'attachment; filename="{filename}"; '
                f"filename*=UTF-8''{filename}"
            ),
            "Content-Length": str(len(document)),
            "Cache-Control": "no-store",
        },
    )