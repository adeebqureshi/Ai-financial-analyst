"""
Maximum Drawdown.
"""

from __future__ import annotations


class MaximumDrawdown:

    def calculate(
        self,
        prices: list[float],
    ) -> float:

        if not prices:
            return 0.0

        peak = prices[0]

        maximum = 0.0

        for price in prices:

            peak = max(
                peak,
                price,
            )

            maximum = max(
                maximum,
                (peak - price) / peak,
            )

        return maximum