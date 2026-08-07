"""
Beta.
"""

from __future__ import annotations


class Beta:

    def calculate(
        self,
        covariance: float,
        market_variance: float,
    ) -> float:

        if market_variance == 0:
            return 0.0

        return covariance / market_variance