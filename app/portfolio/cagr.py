"""
Compound Annual Growth Rate.
"""

from __future__ import annotations


class CAGR:

    def calculate(
        self,
        beginning: float,
        ending: float,
        years: float,
    ) -> float:

        if beginning <= 0 or years <= 0:
            return 0.0

        return (ending / beginning) ** (1 / years) - 1