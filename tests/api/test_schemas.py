from app.api.schemas import AnalyzeRequest
from app.api.schemas import AnalyzeResponse


def test_request():

    request = AnalyzeRequest(
        ticker="AAPL",
        query="Should I buy Apple?",
    )

    assert request.ticker == "AAPL"
    assert request.query == "Should I buy Apple?"


def test_response():

    response = AnalyzeResponse(
        ticker="AAPL",
        report="BUY",
    )

    assert response.ticker == "AAPL"
    assert response.report == "BUY"