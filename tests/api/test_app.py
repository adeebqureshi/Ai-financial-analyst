from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

from app.api.app import FinancialAnalystAPI


@patch("app.api.app.AnalysisRouter")
def test_api(mock_router):

    router = MagicMock()

    router.analyze.return_value = SimpleNamespace(
        ticker="AAPL",
        report="BUY",
    )

    mock_router.return_value = router

    api = FinancialAnalystAPI()

    response = api.analyze(
        ticker="AAPL",
        query="Should I buy Apple?",
        result={},
        context="Revenue increased.",
    )

    assert response.ticker == "AAPL"
    assert response.report == "BUY"