from app.portfolio.analytics import PortfolioAnalytics
from app.portfolio.holding import Holding
from app.portfolio.portfolio import Portfolio


def test_analytics():

    analytics = PortfolioAnalytics()

    portfolio = Portfolio([
        Holding("AAPL", 10, 100),
        Holding("MSFT", 5, 200),
    ])

    summary = analytics.summary(
        portfolio
    )

    assert summary["total_value"] == 2000

    assert summary["average_position"] == 1000