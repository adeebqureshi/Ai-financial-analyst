from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from app.ingestion.clients.yahoo_client import YahooClient


def _stub_ticker(info: dict, history: pd.DataFrame) -> MagicMock:
    """Build a deterministic stand-in for ``yfinance.Ticker``.

    Yahoo Finance (via ``yfinance``) is an unofficial, rate-limited external
    provider without an SLA. Unit tests must never depend on live network
    access, so the client's ``yf`` seam is patched and a canned response object
    is injected instead of issuing a real HTTP request. Production keeps using
    the real ``yfinance`` implementation untouched.
    """
    stock = MagicMock()
    stock.info = info
    stock.history.return_value = history
    return stock


@patch("app.ingestion.clients.yahoo_client.yf.Ticker")
def test_get_info(mock_ticker: MagicMock) -> None:
    mock_ticker.return_value = _stub_ticker(
        {"symbol": "AAPL", "shortName": "Apple Inc.", "currentPrice": 190.0},
        pd.DataFrame(),
    )

    client = YahooClient()
    info = client.get_info("AAPL")

    assert isinstance(info, dict)
    assert "symbol" in info
    assert info["symbol"] == "AAPL"
    mock_ticker.assert_called_once_with("AAPL")


@patch("app.ingestion.clients.yahoo_client.yf.Ticker")
def test_get_history(mock_ticker: MagicMock) -> None:
    frame = pd.DataFrame(
        {"Close": [190.0, 191.5], "Volume": [1_000_000, 1_200_000]},
        index=pd.to_datetime(["2026-01-02", "2026-01-05"]),
    )
    stock = _stub_ticker({"symbol": "AAPL"}, frame)
    mock_ticker.return_value = stock

    client = YahooClient()
    history = client.get_history("AAPL")

    assert not history.empty
    stock.history.assert_called_once_with(period="1y")