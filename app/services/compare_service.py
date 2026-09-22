from __future__ import annotations
from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.assumptions import get_financial_assumptions
from app.financial.data import FinancialDataService
from app.financial.health import FinancialHealth
from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine
from app.schemas.analysis import CompareRequest
from app.schemas.responses import CompareItemData, CompareResponseData
from app.utils.tickers import normalize_ticker
logger = get_logger(__name__)
class CompareService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = ValuationEngine()
        self._financial_data = FinancialDataService()
        self._assumptions = get_financial_assumptions(settings)
    def compare(self, request: CompareRequest) -> CompareResponseData:
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
                current_price=request.valuation.current_price or 0.0,
                growth_rate=request.valuation.growth_rate,
                risk_free_rate=request.valuation.risk_free_rate,
                beta=request.valuation.beta,
                market_return=request.valuation.market_return,
                tax_rate=request.valuation.tax_rate,
                cost_of_debt=request.valuation.cost_of_debt,
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
        best_ticker = max(results, key=lambda item: item.upside).ticker
        return CompareResponseData(
            results=results,
            best=best_ticker,
        )
    def compare_tickers(self, tickers: list[str]) -> CompareResponseData:
        results: list[CompareItemData] = []
        tickers = [normalize_ticker(t) for t in tickers]
        for ticker in tickers:
            data = self._financial_data.load(ticker)
            result = self._engine.evaluate(
                statement=data.statement,
                current_price=data.current_price or 0.0,
                growth_rate=data.growth_rate,
                risk_free_rate=self._assumptions.risk_free_rate,
                beta=data.beta or 1.0,
                market_return=self._assumptions.market_return,
                tax_rate=data.tax_rate,
                cost_of_debt=self._assumptions.cost_of_debt,
                terminal_growth=self._assumptions.terminal_growth,
                years=self._assumptions.projection_years,
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