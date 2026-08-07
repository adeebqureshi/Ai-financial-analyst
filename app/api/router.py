"""
router.py

API router.
"""

from __future__ import annotations

from app.api.schemas import AnalyzeRequest
from app.api.schemas import AnalyzeResponse
from app.llm.report_generator import ReportGenerator


class AnalysisRouter:

    def __init__(self) -> None:

        self.generator = ReportGenerator()

    def analyze(
        self,
        request: AnalyzeRequest,
        result: dict,
        context: str,
    ) -> AnalyzeResponse:

        report = self.generator.generate(
            query=request.query,
            context=context,
            result=result,
        )

        return AnalyzeResponse(
            ticker=request.ticker,
            report=report,
        )