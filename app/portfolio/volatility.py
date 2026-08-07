"""
Volatility.
"""

from __future__ import annotations

import math


class Volatility:

    def calculate(
        self,
        returns: list[float],
    ) -> float:

        if not returns:
            return 0.0

        mean = sum(returns) / len(returns)

        variance = (
            sum((r - mean) ** 2 for r in returns)
            / len(returns)
        )

        return math.sqrt(variance)