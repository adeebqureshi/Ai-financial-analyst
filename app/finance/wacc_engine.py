"""
Weighted Average Cost of Capital calculations.
"""

from __future__ import annotations

from app.finance.wacc import WACC


class WACCEngine:

    def calculate(
        self,
        *,
        risk_free_rate: float,
        beta: float,
        market_return: float,
        cost_of_debt: float,
        tax_rate: float,
        market_value_equity: float,
        market_value_debt: float,
    ) -> WACC:

        cost_of_equity = (
            risk_free_rate
            + beta * (
                market_return
                - risk_free_rate
            )
        )

        after_tax_cost_of_debt = (
            cost_of_debt
            * (1 - tax_rate)
        )

        total_value = (
            market_value_equity
            + market_value_debt
        )

        equity_weight = (
            market_value_equity / total_value
            if total_value
            else 0.0
        )

        debt_weight = (
            market_value_debt / total_value
            if total_value
            else 0.0
        )

        wacc = (
            equity_weight * cost_of_equity
            + debt_weight * after_tax_cost_of_debt
        )

        return WACC(
            cost_of_equity=cost_of_equity,
            after_tax_cost_of_debt=after_tax_cost_of_debt,
            wacc=wacc,
        )