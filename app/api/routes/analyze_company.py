from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/analyze-company",
    tags=["Frontend"],
)


class AnalyzeCompanyRequest(BaseModel):
    ticker: str


@router.post("")
async def analyze_company(
    request: AnalyzeCompanyRequest,
):
    """
    Frontend entrypoint.

    The frontend only provides a ticker.

    This endpoint will orchestrate the entire
    AI Financial Analyst workflow.
    """

    ticker = request.ticker.upper()

    try:
        # TODO
        # Fetch company profile
        # Fetch SEC filings
        # Compute ratios
        # Run DCF
        # Run risk analysis
        # Run LLM report

        return {
            "success": True,
            "message": "Workflow started",
            "data": {
                "ticker": ticker,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )