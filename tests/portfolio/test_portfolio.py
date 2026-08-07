from app.portfolio.holding import Holding
from app.portfolio.portfolio import Portfolio


def test_portfolio():

    portfolio = Portfolio([
        Holding("AAPL", 10, 100),
        Holding("MSFT", 5, 200),
    ])

    assert portfolio.total_value == 2000