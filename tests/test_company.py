import pytest

from app.models.company import Company
from app.models.company import Exchange


def test_company_creation():

    company = Company(
        ticker="aapl",
        cik="320193",
        name="Apple Inc.",
        exchange=Exchange.NASDAQ,
        sector="Technology",
        industry="Consumer Electronics",
        country="United States",
        website="https://www.apple.com",
    )

    assert company.ticker == "AAPL"


def test_invalid_cik():

    with pytest.raises(ValueError):

        Company(
            ticker="AAPL",
            cik="ABC123",
            name="Apple",
            exchange=Exchange.NASDAQ,
            sector="Technology",
            industry="Consumer Electronics",
            country="USA",
        )


def test_invalid_ticker():

    with pytest.raises(ValueError):

        Company(
            ticker="THISISALONGTICKER",
            cik="123456",
            name="Apple",
            exchange=Exchange.NASDAQ,
            sector="Technology",
            industry="Consumer Electronics",
            country="USA",
        )