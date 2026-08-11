"""
Report Service

This module contains the business logic for generating financial reports.
It delegates to the new agentic CoordinatorAgent for structured report generation.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.llm.openai_client import OpenAIClient
from app.schemas.responses import ReportData

logger = get_logger(__name__)


def _get_coordinator(settings: Settings) -> "CoordinatorAgent":
    """Lazy import to avoid circular dependency."""
    from app.agents.coordinator import CoordinatorAgent
    from app.agents.financial_analyst import FinancialAnalystAgent

    llm_client = OpenAIClient()
    analyst = FinancialAnalystAgent(settings, llm_client=llm_client)
    return CoordinatorAgent(settings=settings, analyst=analyst)


class ReportService:
    """
    Service for generating financial reports using the agentic pipeline.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._coordinator = None

    def _get_coordinator_instance(self) -> "CoordinatorAgent":
        if self._coordinator is None:
            self._coordinator = _get_coordinator(self._settings)
        return self._coordinator

    def generate_ticker_report(
        self,
        ticker: str,
        query: str = "",
    ) -> ReportData:
        """
        Generate a report using the agentic research pipeline.

        Args:
            ticker: The ticker symbol (e.g. "AAPL").
            query: Optional report query.

        Returns:
            A ``ReportData`` with the generated report.
        """
        ticker = ticker.upper()
        report_query = query or f"Create a complete investment research report on {ticker} using its financials and annual report."

        coordinator = self._get_coordinator_instance()
        result = coordinator.run_report(
            query=report_query,
            ticker=ticker,
        )

        return ReportData(
            ticker=ticker,
            title=result.report.title,
            content=result.report.body,
            format="markdown",
        )

    def generate(self, ticker: str, query: str = "") -> ReportData:
        """
        Generate a comprehensive financial report (alias for generate_ticker_report).

        Args:
            ticker: The ticker symbol.
            query: Optional report query.

        Returns:
            A ``ReportData`` with the generated report.
        """
        return self.generate_ticker_report(ticker, query)