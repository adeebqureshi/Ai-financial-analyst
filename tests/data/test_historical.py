from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from app.data.historical import HistoricalData


@patch("app.data.historical.yf.Ticker")
def test_history(mock_ticker: MagicMock) -> None:
    """Price history is read through the patched ``yfinance`` seam.

    The live Yahoo Finance endpoint is unofficial and rate-limited, so the
    provider call is stubbed to keep this test deterministic and independent
    of internet availability. The assertion on the returned frame is kept
    intact; production still uses real ``yfinance``.
    """
    mock_ticker.return_value.history.return_value = pd.DataFrame(
        {
            "Open": [190.0, 191.0],
            "High": [192.0, 193.0],
            "Low": [189.0, 190.0],
            "Close": [191.0, 192.5],
            "Volume": [1_000_000, 1_100_000],
        },
        index=pd.to_datetime(["2026-01-02", "2026-01-05"]),
    )

    history = HistoricalData()
    data = history.history(
        "AAPL",
        period="5d",
    )

    assert len(data) > 0
    mock_ticker.assert_called_once_with("AAPL")
    mock_ticker.return_value.history.assert_called_once_with(period="5d")