from __future__ import annotations

from app.portfolio.performance import PerformanceAnalyzer
from app.portfolio.portfolio import Portfolio
from app.portfolio.risk import RiskAnalyzer


class PortfolioAnalytics:

    def __init__(self):

        self.performance = PerformanceAnalyzer()

        self.risk = RiskAnalyzer()

    def summary(
        self,
        portfolio: Portfolio,
    ) -> dict[str, float]:

        return {
            "total_value": portfolio.total_value,
            "average_position": self.performance.average_position(
                portfolio
            ),
            "concentration": self.risk.concentration(
                portfolio
            ),
        }