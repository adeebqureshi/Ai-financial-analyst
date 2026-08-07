from __future__ import annotations

from app.portfolio.portfolio import Portfolio


class RiskAnalyzer:

    def concentration(
        self,
        portfolio: Portfolio,
    ) -> float:

        total = portfolio.total_value

        if total == 0:
            return 0.0

        largest = max(
            h.value
            for h in portfolio.holdings
        )

        return largest / total