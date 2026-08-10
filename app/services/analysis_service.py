"""
Analysis Service

This module contains the business logic for performing comprehensive financial
analysis. It delegates to the existing ``FinancialPipeline`` for multi-agent
orchestration and wraps the results in typed response DTOs.

Design Decisions:
    - **Wraps existing pipeline**: Rather than reimplementing the orchestration
      logic, this service calls ``FinancialPipeline.analyze_company()`` and
      transforms the result dict into a typed ``AnalyzeResponseData``.
    - **Settings injection**: Consistent with ``HealthService`` and
      ``VersionService``, the constructor accepts ``Settings`` for dependency
      injection and testability.
    - **No I/O in constructor**: The ``FinancialPipeline`` is lazily created
      on first call to ``analyze()``, keeping the constructor lightweight.
"""

from __future__ import annotations

from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.analysis import FinancialAnalysisEngine
from app.financial.health import FinancialHealth
from app.financial.models import FinancialStatement
from app.financial.wacc import WACC
from app.orchestrator.pipeline import FinancialPipeline
from app.schemas.analysis import AnalyzeRequest, FinancialStatementInput
from app.schemas.responses import (
    AnalyzeResponseData,
    CompanyData,
    HealthScoreData,
    MarketDataResponse,
    ValuationResultData,
)

logger = get_logger(__name__)


class AnalysisService:
    """
    Service for performing comprehensive financial analysis.

    Attributes:
        _settings: Application settings instance.
        _pipeline: Optional cached financial pipeline instance.
        _engine: Financial analysis engine.
    """

    def __init__(self, settings: Settings) -> None:
        """
        Initialize the analysis service.

        Args:
            settings: The application settings instance.
        """
        self._settings = settings
        self._pipeline: FinancialPipeline | None = None
        self._engine = FinancialAnalysisEngine()

    def _get_pipeline(self) -> FinancialPipeline:
        """
        Lazy-initialize and return the financial pipeline.

        Returns:
            A ``FinancialPipeline`` instance.
        """
        if self._pipeline is None:
            self._pipeline = FinancialPipeline()
        return self._pipeline

    @staticmethod
    def _as_value(value: object) -> str | None:
        """Return the enum value if the value is an enum, else the raw value."""
        if value is None:
            return None
        return getattr(value, "value", value)

    def analyze(self, request: AnalyzeRequest) -> AnalyzeResponseData:
        """
        Perform a comprehensive financial analysis.

        Args:
            request: The validated analysis request.

        Returns:
            An ``AnalyzeResponseData`` with the analysis results.
        """
        pipeline = self._get_pipeline()

        # Build the financial statement from the request
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

        # Run the full pipeline analysis
        result = pipeline.analyze_company(
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

        # Extract the analysis result
        analysis = result.get("analysis", {})
        company = result.get("company", {})
        market = result.get("market", {})

        # Compute the WACC discount rate
        equity = statement.total_assets - statement.total_liabilities
        cost_of_equity = WACC.cost_of_equity(
            risk_free_rate=request.valuation.risk_free_rate,
            beta=request.valuation.beta,
            market_return=request.valuation.market_return,
        )
        try:
            discount_rate = WACC.calculate(
                equity=equity,
                debt=statement.debt,
                cost_of_equity=cost_of_equity,
                cost_of_debt=0.05,
                tax_rate=request.valuation.tax_rate,
            )
        except ValueError:
            discount_rate = 0.0

        # Compute health score
        health_score = FinancialHealth.score(
            request.piotroski_score,
            request.altman_score,
            request.beneish_score,
        )
        health_rating = FinancialHealth.rating(health_score)

        # Build the response
        return AnalyzeResponseData(
            ticker=request.ticker,
            query=request.query,
            company=CompanyData(
                ticker=request.ticker,
                name=getattr(company, "name", request.ticker),
                sector=getattr(company, "sector", None),
                industry=getattr(company, "industry", None),
                market_cap=getattr(company, "market_cap", None),
                description=getattr(company, "description", None),
            ),
            market=MarketDataResponse(
                ticker=getattr(market, "ticker", request.ticker),
                exchange=self._as_value(getattr(market, "exchange", None)),
                current_price=getattr(market, "current_price", 0.0) or 0.0,
                currency=getattr(market, "currency", "USD") or "USD",
                market_cap=getattr(market, "market_cap", None),
                volume=getattr(market, "volume", None),
                beta=getattr(market, "beta", None),
                pe_ratio=getattr(market, "pe_ratio", None),
                eps=getattr(market, "eps", None),
                dividend_yield=getattr(market, "dividend_yield", None),
                week_52_high=getattr(market, "week_52_high", None),
                week_52_low=getattr(market, "week_52_low", None),
            ),
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
            valuation=ValuationResultData(
                intrinsic_value=getattr(analysis, "intrinsic_value", 0.0),
                upside=getattr(analysis, "upside", 0.0),
                recommendation=getattr(analysis, "recommendation", "HOLD"),
                current_price=getattr(market, "current_price", 0.0) or 0.0,
                discount_rate=discount_rate,
            ),
            health=HealthScoreData(
                score=health_score,
                rating=health_rating,
                piotroski_score=request.piotroski_score,
                altman_score=request.altman_score,
                beneish_score=request.beneish_score,
            ),
            recommendation=getattr(analysis, "recommendation", "HOLD"),
        )