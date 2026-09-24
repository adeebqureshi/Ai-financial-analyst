from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from app.data.financials import FinancialStatements


@patch("app.data.financials.yf.Ticker")
def test_financials(mock_ticker: MagicMock) -> None:
    """Statements are read through the patched ``yfinance`` seam.

    Stubbing the provider keeps the test deterministic and independent of
    internet availability, Yahoo rate limits, or Yahoo API changes while the
    original "statements are returned" assertion is preserved and tightened.
    """
    mock_ticker.return_value.financials = pd.DataFrame(
        {"2025-09-30": [416_161.0]},
        index=["Total Revenue"],
    )

    statements = FinancialStatements()
    income = statements.income_statement(
        "AAPL",
    )

    assert income is not None
    assert not income.empty
    mock_ticker.assert_called_once_with("AAPL")