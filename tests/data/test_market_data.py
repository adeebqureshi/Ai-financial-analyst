from app.data.market_data import MarketData


def test_market():

    market = MarketData(
        price=200.0,
        market_cap=3000,
        pe_ratio=30,
        eps=6.5,
        volume=100,
    )

    assert market.price == 200.0

    assert market.volume == 100