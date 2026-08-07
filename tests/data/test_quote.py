from app.data.quote import StockQuote


def test_quote():

    quote = StockQuote(
        symbol="AAPL",
        price=210.0,
        previous_close=205.0,
        change=5.0,
        change_percent=2.43,
    )

    assert quote.symbol == "AAPL"

    assert quote.price > 0