"""
Report Service

This module contains the business logic for generating financial reports.
It delegates to the existing ``ReportGenerator`` and ``FinancialPipeline``.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.data import FinancialDataService
from app.financial.models import FinancialStatement
from app.llm.report_generator import ReportGenerator
from app.orchestrator.pipeline import FinancialPipeline
from app.schemas.analysis import FinancialStatementInput, ReportRequest, ValuationParams
from app.schemas.responses import ReportData

logger = get_logger(__name__)

_RISK_FREE_RATE = 0.0425
_MARKET_RETURN = 0.10


class ReportService:
    """
    Service for generating financial reports.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._pipeline = FinancialPipeline()
        self._generator = ReportGenerator()
        self._financial_data = FinancialDataService()

    def generate_ticker_report(
        self,
        ticker: str,
        query: str = "",
    ) -> ReportData:
        """
        Generate a report using real, company-specific financial data.

        Args:
            ticker: The ticker symbol (e.g. ``"AAPL"``).
            query: Optional report query.

        Returns:
            A ``ReportData`` with the generated report.
        """
        ticker = ticker.upper()
        data = self._financial_data.load(ticker)
        statement = data.statement

        request = ReportRequest(
            ticker=ticker,
            query=query or f"Generate a comprehensive financial report for {ticker}",
            statement=FinancialStatementInput(
                revenue=statement.revenue,
                operating_income=statement.operating_income,
                net_income=statement.net_income,
                total_assets=statement.total_assets,
                total_liabilities=statement.total_liabilities,
                cash=statement.cash,
                debt=statement.debt,
                shares_outstanding=statement.shares_outstanding,
                free_cash_flow=statement.free_cash_flow,
            ),
            valuation=ValuationParams(
                current_price=data.current_price or 1.0,
                growth_rate=data.growth_rate,
                risk_free_rate=_RISK_FREE_RATE,
                beta=data.beta or 1.0,
                market_return=_MARKET_RETURN,
                tax_rate=data.tax_rate,
            ),
            piotroski_score=data.piotroski_score,
            altman_score=data.altman_score,
            beneish_score=data.beneish_score,
        )

        return self.generate(request)

    def generate(self, request: ReportRequest) -> ReportData:
        """
        Generate a comprehensive financial report.

        Args:
            request: The validated report request.

        Returns:
            A ``ReportData`` with the generated report.
        """
        statement = FinancialStatement(
            revenue=request.statement.revenue,
            operating_income=request.statement.operating_income,
            net_income=request.statement.net_income,
            total_assets=request.statement.total_assets,
            total_liabilities=request.statement.total_liabilities,
            cash=request.statement.cash,
            debt=request.statement.debt,
            shares_outstanding=request.statement.shares_outstanding,
            free_cash_flow=request.statement.free_cash_flow,
        )

        # Run the pipeline to get analysis data
        result = self._pipeline.analyze_company(
            ticker=request.ticker,
            statement=statement,
            query=request.query,
            growth_rate=request.valuation.growth_rate,
            risk_free_rate=request.valuation.risk_free_rate,
            beta=request.valuation.beta,
            market_return=request.valuation.market_return,
            tax_rate=request.valuation.tax_rate,
            piotroski_score=request.piotroski_score,
            altman_score=request.altman_score,
            beneish_score=request.beneish_score,
        )

        # Generate the LLM-powered report
        report = self._generator.generate(
            query=request.query,
            context=str(result.get("context", "")),
            result=result,
        )

        return ReportData(
            ticker=request.ticker,
            title=f"{request.ticker} Financial Report",
            content=report,
            format="markdown",
        )