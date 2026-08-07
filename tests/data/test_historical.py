from app.data.historical import HistoricalData


def test_history():

    history = HistoricalData()

    data = history.history(
        "AAPL",
        period="5d",
    )

    assert len(data) > 0