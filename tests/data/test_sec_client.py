from app.data.sec_client import SECClient


def test_sec_client():

    client = SECClient()

    company = client.company(
        "AAPL",
    )

    assert company.ticker == "AAPL"

    assert "Apple" in company.title