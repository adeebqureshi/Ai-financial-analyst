"""
Valuation Service

This module contains the business logic for performing DCF valuation.
It delegates to the existing ``ValuationEngine`` and wraps the results
in typed response DTOs.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine
from app.schemas.analysis import ValuationRequest, IntrinsicValueRequest
from app.schemas.responses import ValuationResultData, IntrinsicValueResponseData, ValuationResponseData

logger = get_logger(__name__)


class ValuationService:
    """
    Service for performing DCF valuation.

    Attributes:
        _settings: Application settings instance.
        _engine: Valuation engine instance.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = ValuationEngine()

    def _build_statement(self, request: ValuationRequest | IntrinsicValueRequest) -> FinancialStatement:
        """Build a FinancialStatement from request data."""
        return FinancialStatement(
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

    def valuate(self, request: ValuationRequest) -> ValuationResponseData:
        """
        Perform a full DCF valuation.

        Args:
            request: The validated valuation request.

        Returns:
            A ``ValuationResponseData`` with the valuation result.
        """
        statement = self._build_statement(request)
        result = self._engine.evaluate(
            statement=statement,
            current_price=request.params.current_price,
            growth_rate=request.params.growth_rate,
            risk_free_rate=request.params.risk_free_rate,
            beta=request.params.beta,
            market_return=request.params.market_return,
            tax_rate=request.params.tax_rate,
            terminal_growth=request.params.terminal_growth,
            years=request.params.years,
        )
        return ValuationResponseData(
            valuation=ValuationResultData(
                intrinsic_value=result.intrinsic_value,
                upside=result.upside,
                recommendation=result.recommendation,
                current_price=request.params.current_price,
                discount_rate=0.0,
            ),
        )

    def intrinsic_value(self, request: IntrinsicValueRequest) -> IntrinsicValueResponseData:
        """
        Calculate intrinsic value per share.

        Args:
            request: The validated intrinsic value request.

        Returns:
            An ``IntrinsicValueResponseData`` with the intrinsic value.
        """
        statement = self._build_statement(request)
        result = self._engine.evaluate(
            statement=statement,
            current_price=request.params.current_price,
            growth_rate=request.params.growth_rate,
            risk_free_rate=request.params.risk_free_rate,
            beta=request.params.beta,
            market_return=request.params.market_return,
            tax_rate=request.params.tax_rate,
            terminal_growth=request.params.terminal_growth,
            years=request.params.years,
        )
        return IntrinsicValueResponseData(
            intrinsic_value=result.intrinsic_value,
            current_price=request.params.current_price,
            upside=result.upside,
        )