"""Tests for the MarketData domain model."""

from app.enums.exchange import Exchange
from app.models.market import MarketData


def test_market_data() -> None:
    """Test instantiation and field values for MarketData."""
    market = MarketData(
        ticker="AAPL",
        exchange=Exchange.NASDAQ,
        current_price=210.52,
        market_cap=3.2e12,
        volume=45123123,
    )

    assert market.ticker == "AAPL"
    assert market.exchange == Exchange.NASDAQ
    assert market.current_price == 210.52
    assert market.market_cap == 3.2e12
    assert market.volume == 45123123
    assert market.currency == "USD"