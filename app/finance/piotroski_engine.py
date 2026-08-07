"""
Piotroski F-Score engine.
"""

from __future__ import annotations

from app.finance.piotroski import PiotroskiScore


class PiotroskiEngine:

    def calculate(
        self,
        *,
        roa_positive: bool,
        operating_cash_flow_positive: bool,
        roa_improved: bool,
        cash_flow_exceeds_income: bool,
        lower_leverage: bool,
        improved_liquidity: bool,
        no_new_shares: bool,
        improved_margin: bool,
        improved_asset_turnover: bool,
    ) -> PiotroskiScore:

        score = sum(
            [
                roa_positive,
                operating_cash_flow_positive,
                roa_improved,
                cash_flow_exceeds_income,
                lower_leverage,
                improved_liquidity,
                no_new_shares,
                improved_margin,
                improved_asset_turnover,
            ]
        )

        return PiotroskiScore(
            score=score,
        )