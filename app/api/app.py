"""
app.py

Main API application.
"""

from __future__ import annotations

from app.api.router import AnalysisRouter
from app.api.schemas import AnalyzeRequest


class FinancialAnalystAPI:

    def __init__(self) -> None:

        self.router = AnalysisRouter()

    def analyze(
        self,
        ticker: str,
        query: str,
        result: dict,
        context: str,
    ):

        request = AnalyzeRequest(
            ticker=ticker,
            query=query,
        )

        return self.router.analyze(
            request=request,
            result=result,
            context=context,
        )