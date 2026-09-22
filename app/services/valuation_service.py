from __future__ import annotations
from app.core.config import Settings
from app.core.logging import get_logger
from app.financial.models import FinancialStatement
from app.financial.valuation import ValuationEngine
from app.financial.wacc import WACC
from app.schemas.analysis import ValuationRequest, IntrinsicValueRequest
from app.schemas.responses import ValuationResultData, IntrinsicValueResponseData, ValuationResponseData
logger = get_logger(__name__)
class ValuationService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._engine = ValuationEngine()
    def _build_statement(self, request: ValuationRequest | IntrinsicValueRequest) -> FinancialStatement:
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
        statement = self._build_statement(request)
        result = self._engine.evaluate(
            statement=statement,
            current_price=request.params.current_price or 0.0,
            growth_rate=request.params.growth_rate,
            risk_free_rate=request.params.risk_free_rate,
            beta=request.params.beta,
            market_return=request.params.market_return,
            tax_rate=request.params.tax_rate,
            cost_of_debt=request.params.cost_of_debt,
            terminal_growth=request.params.terminal_growth,
            years=request.params.years,
        )
        return ValuationResponseData(
            valuation=ValuationResultData(
                intrinsic_value=result.intrinsic_value,
                upside=result.upside,
                recommendation=result.recommendation,
                current_price=request.params.current_price,
                discount_rate=self._compute_discount_rate(request),
                assumptions_source="request",
                risk_free_rate=request.params.risk_free_rate,
                market_return=request.params.market_return,
                cost_of_debt=request.params.cost_of_debt,
            ),
        )
    def _compute_discount_rate(
        self,
        request: ValuationRequest | IntrinsicValueRequest,
    ) -> float:
        statement = self._build_statement(request)
        equity = statement.total_assets - statement.total_liabilities
        cost_of_equity = WACC.cost_of_equity(
            risk_free_rate=request.params.risk_free_rate,
            beta=request.params.beta,
            market_return=request.params.market_return,
        )
        try:
            return WACC.calculate(
                equity=equity,
                debt=statement.debt,
                cost_of_equity=cost_of_equity,
                cost_of_debt=request.params.cost_of_debt,
                tax_rate=request.params.tax_rate,
            )
        except ValueError:
            return 0.0
    def intrinsic_value(self, request: IntrinsicValueRequest) -> IntrinsicValueResponseData:
        statement = self._build_statement(request)
        result = self._engine.evaluate(
            statement=statement,
            current_price=request.params.current_price or 0.0,
            growth_rate=request.params.growth_rate,
            risk_free_rate=request.params.risk_free_rate,
            beta=request.params.beta,
            market_return=request.params.market_return,
            tax_rate=request.params.tax_rate,
            cost_of_debt=request.params.cost_of_debt,
            terminal_growth=request.params.terminal_growth,
            years=request.params.years,
        )
        return IntrinsicValueResponseData(
            intrinsic_value=result.intrinsic_value,
            current_price=request.params.current_price,
            upside=result.upside,
        )