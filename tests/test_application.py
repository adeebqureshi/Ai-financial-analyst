from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from app.application import Application


@patch("app.application.FinancialAnalystAPI")
def test_application(mock_api):

    api = MagicMock()

    api.analyze.return_value = SimpleNamespace(
        ticker="AAPL",
        report="BUY",
    )

    mock_api.return_value = api

    app = Application()

    response = app.analyze(
        ticker="AAPL",
        query="Should I buy Apple?",
        result={},
        context="Revenue increased.",
    )

    assert response.ticker == "AAPL"
    assert response.report == "BUY"

    api.analyze.assert_called_once()