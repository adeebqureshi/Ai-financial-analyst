from app.ingestion.clients.yahoo_client import YahooClient


def test_get_info():

    client = YahooClient()

    info = client.get_info("AAPL")

    assert isinstance(info, dict)

    assert "symbol" in info


def test_get_history():

    client = YahooClient()

    history = client.get_history("AAPL")

    assert not history.empty