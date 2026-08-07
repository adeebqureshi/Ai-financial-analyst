"""
altman.py

Altman Z-Score bankruptcy prediction model.
"""

from __future__ import annotations


class AltmanZScore:

    @staticmethod
    def calculate(
        working_capital: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,
        total_liabilities: float,
        sales: float,
        total_assets: float,
    ) -> float:

        if total_assets <= 0:
            raise ValueError(
                "Total assets must be positive."
            )

        if total_liabilities <= 0:
            raise ValueError(
                "Total liabilities must be positive."
            )

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_value_equity / total_liabilities
        x5 = sales / total_assets

        return (
            1.2 * x1
            + 1.4 * x2
            + 3.3 * x3
            + 0.6 * x4
            + 1.0 * x5
        )

    @staticmethod
    def interpretation(
        score: float,
    ) -> str:

        if score > 2.99:
            return "SAFE"

        if score >= 1.81:
            return "GREY"

        return "DISTRESS"