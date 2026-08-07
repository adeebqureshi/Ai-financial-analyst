"""
valuation.py

High-level financial valuation engine.
"""

from __future__ import annotations

from app.financial.dcf import DCFValuation
from app.financial.models import FinancialStatement
from app.financial.models import ValuationResult
from app.financial.wacc import WACC


class ValuationEngine:

    def evaluate(
        self,
        statement: FinancialStatement,
        current_price: float,
        growth_rate: float,
        risk_free_rate: float,
        beta: float,
        market_return: float,
        tax_rate: float,
        terminal_growth: float = 0.03,
        years: int = 5,
    ) -> ValuationResult:

        equity = (
            statement.total_assets
            - statement.total_liabilities
        )

        cost_of_equity = WACC.cost_of_equity(
            risk_free_rate=risk_free_rate,
            beta=beta,
            market_return=market_return,
        )

        cost_of_debt = 0.05

        discount_rate = WACC.calculate(
            equity=equity,
            debt=statement.debt,
            cost_of_equity=cost_of_equity,
            cost_of_debt=cost_of_debt,
            tax_rate=tax_rate,
        )

        intrinsic = DCFValuation.intrinsic_value(
            free_cash_flow=statement.free_cash_flow,
            growth_rate=growth_rate,
            discount_rate=discount_rate,
            terminal_growth=terminal_growth,
            years=years,
            shares_outstanding=statement.shares_outstanding,
        )

        upside = (
            (intrinsic - current_price)
            / current_price
        ) * 100

        if upside >= 20:
            recommendation = "STRONG BUY"
        elif upside >= 10:
            recommendation = "BUY"
        elif upside >= -10:
            recommendation = "HOLD"
        else:
            recommendation = "SELL"

        return ValuationResult(
            intrinsic_value=intrinsic,
            upside=upside,
            recommendation=recommendation,
        )