"""
Sharpe Ratio.
"""

from __future__ import annotations

import math


class SharpeRatio:

    def calculate(
        self,
        returns: list[float],
        risk_free_rate: float = 0.02,
    ) -> float:

        if not returns:
            return 0.0

        mean = sum(returns) / len(returns)

        variance = (
            sum((r - mean) ** 2 for r in returns)
            / len(returns)
        )

        std = math.sqrt(variance)

        if std == 0:
            return 0.0

        return (mean - risk_free_rate) / std