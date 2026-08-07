"""
Correlation.
"""

from __future__ import annotations


class Correlation:

    def calculate(
        self,
        x: list[float],
        y: list[float],
    ) -> float:

        if len(x) != len(y) or len(x) == 0:
            return 0.0

        mx = sum(x) / len(x)
        my = sum(y) / len(y)

        numerator = sum(
            (a - mx) * (b - my)
            for a, b in zip(x, y)
        )

        dx = sum(
            (a - mx) ** 2
            for a in x
        )

        dy = sum(
            (b - my) ** 2
            for b in y
        )

        denominator = (dx * dy) ** 0.5

        if denominator == 0:
            return 0.0

        return numerator / denominator