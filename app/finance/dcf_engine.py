"""
Discounted Cash Flow valuation engine.
"""

from __future__ import annotations

from app.finance.dcf import DCFValuation


class DCFEngine:

    def calculate(
        self,
        *,
        free_cash_flow: float,
        growth_rate: float,
        discount_rate: float,
        terminal_growth_rate: float,
        years: int,
        cash: float,
        debt: float,
        shares_outstanding: float,
    ) -> DCFValuation:

        present_value = 0.0

        fcf = free_cash_flow

        for year in range(1, years + 1):

            fcf *= 1 + growth_rate

            present_value += (
                fcf
                / ((1 + discount_rate) ** year)
            )

        terminal_fcf = fcf * (
            1 + terminal_growth_rate
        )

        terminal_value = (
            terminal_fcf
            / (
                discount_rate
                - terminal_growth_rate
            )
        )

        terminal_value /= (
            (1 + discount_rate) ** years
        )

        enterprise_value = (
            present_value
            + terminal_value
        )

        equity_value = (
            enterprise_value
            + cash
            - debt
        )

        intrinsic = (
            equity_value
            / shares_outstanding
            if shares_outstanding
            else 0.0
        )

        return DCFValuation(
            enterprise_value=enterprise_value,
            equity_value=equity_value,
            intrinsic_value_per_share=intrinsic,
        )