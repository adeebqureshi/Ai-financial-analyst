from app.portfolio.holding import Holding


def test_holding():

    holding = Holding(
        "AAPL",
        10,
        200,
    )

    assert holding.value == 2000