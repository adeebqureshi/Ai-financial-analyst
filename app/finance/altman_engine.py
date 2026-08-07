"""
Altman Z-Score engine.
"""

from __future__ import annotations

from app.finance.altman import AltmanZScore


class AltmanEngine:

    def calculate(
        self,
        *,
        working_capital: float,
        retained_earnings: float,
        ebit: float,
        market_value_equity: float,
        total_liabilities: float,
        sales: float,
        total_assets: float,
    ) -> AltmanZScore:

        if total_assets == 0 or total_liabilities == 0:
            return AltmanZScore(score=0.0)

        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit / total_assets
        x4 = market_value_equity / total_liabilities
        x5 = sales / total_assets

        score = (
            1.2 * x1
            + 1.4 * x2
            + 3.3 * x3
            + 0.6 * x4
            + 1.0 * x5
        )

        return AltmanZScore(score=score)