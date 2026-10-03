"""Live SEC EDGAR integration tests.

These exercise the real ``SECService`` against the public EDGAR API, so they
require internet access and are excluded from the default offline suite. They
are retained (not removed) as genuine integration coverage: run them with

    pytest -m integration
"""

import pytest

from app.ingestion.services.sec_service import SECService
from app.models.company import Company

pytestmark = pytest.mark.integration
def test_get_company():
    service = SECService()
    company = service.get_company("AAPL")
    assert isinstance(company, Company)
    assert company.ticker
def test_get_latest_filings():
    service = SECService()
    filings = service.get_latest_filings(
        ticker="AAPL",
        form="10-K",
        limit=2,
    )
    assert len(filings) <= 2
