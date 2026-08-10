"""
Compare Service

This module contains the business logic for comparing multiple companies.
It delegates to the existing ``ValuationEngine`` and ``FinancialHealth``
engines. Each ticker is analyzed with its own real, company-specific
financial data — one company's statement is never reused for another.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.data import FinancialDataService
from app.financial.health import FinancialHealth
from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine
from app.schemas.analysis import CompareRequest
from app.schemas.responses import CompareItemData, CompareResponseData

logger = get_logger(__name__)

_RISK_FREE_RATE = 0.0425
_MARKET_RETURN = 0.10


class CompareService:
    """
    Service for comparing multiple companies.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = ValuationEngine()
        self._financial_data = FinancialDataService()

    def compare(self, request: CompareRequest) -> CompareResponseData:
        """
        Compare multiple tickers using the provided financial statement.

        Kept for backward compatibility with callers that supply an explicit
        ``CompareRequest``. New callers should use :meth:`compare_tickers`.

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

    def compare_tickers(self, tickers: list[str]) -> CompareResponseData:
        """
        Compare multiple tickers using each company's own real financial data.

        For every ticker the service fetches its actual financial statements,
        market data, risk scores and growth rate, then runs the valuation and
        health engines on that company-specific data.

        Args:
            tickers: List of 2-10 ticker symbols.

        Returns:
            A ``CompareResponseData`` with per-ticker results.

        Raises:
            RetrievalError: If a provider cannot supply data for any ticker.
        """
        results: list[CompareItemData] = []

        for ticker in tickers:
            data = self._financial_data.load(ticker)

            result = self._engine.evaluate(
                statement=data.statement,
                current_price=data.current_price,
                growth_rate=data.growth_rate,
                risk_free_rate=_RISK_FREE_RATE,
                beta=data.beta or 1.0,
                market_return=_MARKET_RETURN,
                tax_rate=data.tax_rate,
            )

            health_score = FinancialHealth.score(
                data.piotroski_score,
                data.altman_score,
                data.beneish_score,
            )

            results.append(
                CompareItemData(
                    ticker=ticker,
                    name=data.name,
                    intrinsic_value=result.intrinsic_value,
                    upside=result.upside,
                    recommendation=result.recommendation,
                    health_score=health_score,
                )
            )

        best_ticker = max(results, key=lambda item: item.upside).ticker

        return CompareResponseData(
            results=results,
            best=best_ticker,
        )
