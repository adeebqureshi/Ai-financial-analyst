"""
Compare Service

This module contains the business logic for comparing multiple companies.
It delegates to the existing ``ValuationEngine``.
"""

from __future__ import annotations

from app.core.config import Settings
from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine
from app.schemas.analysis import CompareRequest
from app.schemas.responses import CompareItemData, CompareResponseData


class CompareService:
    """
    Service for comparing multiple companies.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = ValuationEngine()

    def compare(self, request: CompareRequest) -> CompareResponseData:
        """
        Compare multiple tickers using the same financial statement.

        Args:
            request: The validated compare request.

        Returns:
            A ``CompareResponseData`` with per-ticker results.
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

        results: list[CompareItemData] = []

        for ticker in request.tickers:
            result = self._engine.evaluate(
                statement=statement,
                current_price=request.valuation.current_price,
                growth_rate=request.valuation.growth_rate,
                risk_free_rate=request.valuation.risk_free_rate,
                beta=request.valuation.beta,
                market_return=request.valuation.market_return,
                tax_rate=request.valuation.tax_rate,
                terminal_growth=request.valuation.terminal_growth,
                years=request.valuation.years,
            )
            results.append(
                CompareItemData(
                    ticker=ticker,
                    name=ticker,
                    intrinsic_value=result.intrinsic_value,
                    upside=result.upside,
                    recommendation=result.recommendation,
                )
            )

        # Determine the best ticker by upside
        best_ticker = max(results, key=lambda item: item.upside).ticker

        return CompareResponseData(
            results=results,
            best=best_ticker,
        )