"""
growth.py

Growth metric calculations.
"""

from __future__ import annotations


class GrowthMetrics:

    @staticmethod
    def growth_rate(
        previous: float,
        current: float,
    ) -> float:

        if previous <= 0:
            raise ValueError(
                "Previous value must be positive."
            )

        return (current - previous) / previous

    @staticmethod
    def cagr(
        beginning: float,
        ending: float,
        years: int,
    ) -> float:

        if beginning <= 0:
            raise ValueError(
                "Beginning value must be positive."
            )

        if years <= 0:
            raise ValueError(
                "Years must be positive."
            )

        return (
            (ending / beginning) ** (1 / years)
        ) - 1

    @staticmethod
    def revenue_growth(
        previous_revenue: float,
        current_revenue: float,
    ) -> float:

        return GrowthMetrics.growth_rate(
            previous_revenue,
            current_revenue,
        )

    @staticmethod
    def earnings_growth(
        previous_income: float,
        current_income: float,
    ) -> float:

        return GrowthMetrics.growth_rate(
            previous_income,
            current_income,
        )

    @staticmethod
    def free_cash_flow_growth(
        previous_fcf: float,
        current_fcf: float,
    ) -> float:

        return GrowthMetrics.growth_rate(
            previous_fcf,
            current_fcf,
        )