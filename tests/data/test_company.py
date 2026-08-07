from app.data.company import Company


def test_company():

    company = Company(
        ticker="AAPL",
        name="Apple Inc.",
        sector="Technology",
        industry="Consumer Electronics",
        exchange="NASDAQ",
    )

    assert company.ticker == "AAPL"

    assert company.exchange == "NASDAQ"