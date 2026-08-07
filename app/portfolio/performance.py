from __future__ import annotations

from app.portfolio.portfolio import Portfolio


class PerformanceAnalyzer:

    def average_position(
        self,
        portfolio: Portfolio,
    ) -> float:

        if not portfolio.holdings:
            return 0.0

        return (
            portfolio.total_value
            / len(portfolio.holdings)
        )