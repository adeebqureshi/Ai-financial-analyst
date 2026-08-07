"""
wacc.py

Weighted Average Cost of Capital.
"""

from __future__ import annotations


class WACC:

    @staticmethod
    def calculate(
        equity: float,
        debt: float,
        cost_of_equity: float,
        cost_of_debt: float,
        tax_rate: float,
    ) -> float:
        """
        Calculate Weighted Average Cost of Capital.
        """

        total_capital = equity + debt

        if total_capital <= 0:
            raise ValueError(
                "Total capital must be positive."
            )

        equity_weight = equity / total_capital

        debt_weight = debt / total_capital

        return (
            equity_weight * cost_of_equity
            + debt_weight * cost_of_debt * (1 - tax_rate)
        )

    @staticmethod
    def cost_of_equity(
        risk_free_rate: float,
        beta: float,
        market_return: float,
    ) -> float:
        """
        CAPM:
        Re = Rf + Beta × (Rm − Rf)
        """

        return (
            risk_free_rate
            + beta * (market_return - risk_free_rate)
        )

    @staticmethod
    def after_tax_cost_of_debt(
        cost_of_debt: float,
        tax_rate: float,
    ) -> float:

        return cost_of_debt * (1 - tax_rate)