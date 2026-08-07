"""
dcf.py

Discounted Cash Flow valuation.
"""

from __future__ import annotations


class DCFValuation:

    @staticmethod
    def intrinsic_value(
        free_cash_flow: float,
        growth_rate: float,
        discount_rate: float,
        terminal_growth: float,
        years: int,
        shares_outstanding: float,
    ) -> float:

        if shares_outstanding <= 0:
            raise ValueError(
                "Shares outstanding must be positive."
            )

        if discount_rate <= terminal_growth:
            raise ValueError(
                "Discount rate must exceed terminal growth."
            )

        present_value = 0.0

        fcf = free_cash_flow

        for year in range(1, years + 1):

            fcf *= (1 + growth_rate)

            present_value += (
                fcf
                / ((1 + discount_rate) ** year)
            )

        terminal_fcf = (
            fcf
            * (1 + terminal_growth)
        )

        terminal_value = (
            terminal_fcf
            / (discount_rate - terminal_growth)
        )

        terminal_value /= (
            (1 + discount_rate) ** years
        )

        enterprise_value = (
            present_value
            + terminal_value
        )

        return (
            enterprise_value
            / shares_outstanding
        )