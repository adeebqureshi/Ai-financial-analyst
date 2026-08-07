from app.portfolio.holding import Holding
from app.portfolio.portfolio import Portfolio
from app.portfolio.risk import RiskAnalyzer


def test_risk():

    analyzer = RiskAnalyzer()

    portfolio = Portfolio([
        Holding("AAPL", 10, 100),
        Holding("MSFT", 5, 100),
    ])

    assert analyzer.concentration(
        portfolio
    ) > 0