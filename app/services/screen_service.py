"""
Screen Service

This module contains the business logic for screening companies based on
financial health criteria. It delegates to the existing ``ValuationEngine``
and ``FinancialHealth`` engines.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.health import FinancialHealth
from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine
from app.schemas.analysis import ScreenRequest
from app.schemas.responses import ScreenItemData, ScreenResponseData

logger = get_logger(__name__)


class ScreenService:
    """
    Service for screening companies based on financial criteria.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = ValuationEngine()

    def screen(self, request: ScreenRequest) -> ScreenResponseData:
        """
        Screen companies against the provided criteria.

        Args:
            request: The validated screening request (includes the candidate
                financial statement and valuation parameters).

        Returns:
            A ``ScreenResponseData`` with matching results.
        """
        # Build the financial statement
        fs = FinancialStatement(
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

        # Run the valuation for the candidate
        result = self._engine.evaluate(
            statement=fs,
            current_price=request.valuation.current_price,
            growth_rate=request.valuation.growth_rate,
            risk_free_rate=request.valuation.risk_free_rate,
            beta=request.valuation.beta,
            market_return=request.valuation.market_return,
            tax_rate=request.valuation.tax_rate,
            terminal_growth=request.valuation.terminal_growth,
            years=request.valuation.years,
        )

        # Compute health from the screening thresholds
        piotroski_score = request.min_piotroski
        altman_score = request.min_altman
        beneish_score = request.max_beneish

        health_score = FinancialHealth.score(piotroski_score, altman_score, beneish_score)
        health_rating = FinancialHealth.rating(health_score)

        results: list[ScreenItemData] = []

        # Check if the candidate passes the filter criteria
        if (
            health_score >= request.min_piotroski * 10
            and result.upside >= request.min_upside
        ):
            results.append(
                ScreenItemData(
                    ticker="UNKNOWN",
                    name="Screen Candidate",
                    piotroski_score=piotroski_score,
                    altman_score=altman_score,
                    beneish_score=beneish_score,
                    health_score=health_score,
                    health_rating=health_rating,
                    intrinsic_value=result.intrinsic_value,
                    upside=result.upside,
                    recommendation=result.recommendation,
                )
            )

        return ScreenResponseData(
            results=results,
            total=len(results),
        )