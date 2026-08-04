from app.enums.exchange import Exchange
from app.models.market import MarketData


def test_market_data():

    market = MarketData(
        ticker="AAPL",
        exchange=Exchange.NASDAQ,
        current_price=210.52,
        market_cap=3.2e12,
        volume=45123123,
    )

    assert market.current_price == 210.52

    assert market.snapshot_time is not None