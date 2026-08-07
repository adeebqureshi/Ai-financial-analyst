from app.data.sec_company import SECCompany


def test_company():

    company = SECCompany(
        cik="320193",
        ticker="AAPL",
        title="Apple Inc.",
    )

    assert company.ticker == "AAPL"

    assert company.cik == "320193"