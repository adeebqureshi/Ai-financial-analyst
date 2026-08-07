from app.portfolio.holding import Holding
from app.portfolio.performance import PerformanceAnalyzer
from app.portfolio.portfolio import Portfolio


def test_performance():

    analyzer = PerformanceAnalyzer()

    portfolio = Portfolio([
        Holding("AAPL", 10, 100),
        Holding("MSFT", 10, 200),
    ])

    assert analyzer.average_position(
        portfolio
    ) == 1500