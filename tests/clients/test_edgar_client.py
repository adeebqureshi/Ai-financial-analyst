"""Hermetic unit tests for :class:`EdgarClient`.

The client is a thin wrapper around the ``edgartools`` library. These unit
tests mock the underlying SEC tooling so they run offline and never require
the live EDGAR service/network.
"""

from unittest.mock import MagicMock, patch

from app.ingestion.clients.edgar_client import EdgarClient


@patch("app.ingestion.clients.edgar_client.settings", edgar_identity="unit-test")
@patch("app.ingestion.clients.edgar_client.Company")
def test_get_company(mock_company, mock_settings):
    mock_company.return_value = MagicMock()

    client = EdgarClient()
    company = client.get_company("AAPL")

    assert company is not None

    mock_company.assert_called_once_with("AAPL")


@patch("app.ingestion.clients.edgar_client.settings", edgar_identity="unit-test")
@patch("app.ingestion.clients.edgar_client.Company")
def test_get_filings(mock_company, mock_settings):
    company = MagicMock()
    company.get_filings.return_value = [MagicMock(), MagicMock(), MagicMock()]
    mock_company.return_value = company

    client = EdgarClient()
    filings = client.get_filings(
        ticker="AAPL",
        form="10-K",
        limit=2,
    )

    assert len(filings) <= 2

    mock_company.assert_called_once_with("AAPL")
    company.get_filings.assert_called_once_with(form="10-K")