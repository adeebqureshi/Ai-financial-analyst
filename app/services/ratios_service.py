from __future__ import annotations
from app.core.config import Settings
from app.financial.models import FinancialStatement
from app.financial.ratios import FinancialRatios
from app.schemas.analysis import FinancialRatiosRequest
from app.schemas.responses import FinancialRatiosData
class RatiosService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
    def compute(self, request: FinancialRatiosRequest) -> FinancialRatiosData:
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
        return FinancialRatiosData(
            debt_to_equity=FinancialRatios.debt_to_equity(statement),
            return_on_assets=FinancialRatios.return_on_assets(statement),
            return_on_equity=FinancialRatios.return_on_equity(statement),
            operating_margin=FinancialRatios.operating_margin(statement),
            net_margin=FinancialRatios.net_margin(statement),
        )