"""
piotroski.py

Piotroski F-Score.
"""

from __future__ import annotations


class Piotroski:

    @staticmethod
    def calculate(
        roa: float,
        operating_cash_flow: float,
        change_in_roa: float,
        accrual: float,
        change_in_leverage: float,
        change_in_liquidity: float,
        equity_issued: bool,
        change_in_gross_margin: float,
        change_in_asset_turnover: float,
    ) -> int:

        score = 0

        score += int(roa > 0)
        score += int(operating_cash_flow > 0)
        score += int(change_in_roa > 0)
        score += int(accrual > 0)
        score += int(change_in_leverage < 0)
        score += int(change_in_liquidity > 0)
        score += int(not equity_issued)
        score += int(change_in_gross_margin > 0)
        score += int(change_in_asset_turnover > 0)

        return score