from fastapi.testclient import TestClient

from app.api.dependencies.services import get_analysis_service
from app.main import app
from app.schemas.responses import AnalyzeResponseData

client = TestClient(app)


def _build_analysis(ticker: str = "AAPL") -> AnalyzeResponseData:
    return AnalyzeResponseData(
        ticker=ticker,
        query=f"Analyze {ticker}",
        company={
            "ticker": ticker,
            "name": "Apple",
        },
        market={
            "ticker": ticker,
            "current_price": 200.0,
            "currency": "USD",
        },
        statement={
            "revenue": 400_000.0,
            "operating_income": 120_000.0,
            "net_income": 100_000.0,
            "total_assets": 350_000.0,
            "total_liabilities": 250_000.0,
            "cash": 25_000.0,
            "debt": 100_000.0,
            "shares_outstanding": 15_000.0,
            "free_cash_flow": 90_000.0,
        },
        valuation={
            "intrinsic_value": 250.0,
            "upside": 25.0,
            "recommendation": "BUY",
            "current_price": 200.0,
            "discount_rate": 0.09,
        },
        health={
            "score": 8,
            "rating": "GOOD",
            "piotroski_score": 8,
            "altman_score": 3.5,
            "beneish_score": -2.4,
        },
        recommendation="BUY",
    )


def test_analyze_company_delegates_to_analysis_service():
    analysis = _build_analysis()
    captured = {}

    class _FakeAnalysisService:
        def analyze_ticker(self, ticker, query=None):
            captured["ticker"] = ticker
            captured["query"] = query
            return analysis

    app.dependency_overrides[get_analysis_service] = lambda: _FakeAnalysisService()

    try:
        response = client.post(
            "/analyze-company",
            json={"ticker": "aapl"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True

    assert captured["ticker"] == "AAPL"

    assert payload["data"]["ticker"] == "AAPL"

    assert payload["data"]["company"]["name"] == "Apple"

    assert payload["data"]["recommendation"] == "BUY"


def test_analyze_company_validates_ticker():
    response = client.post(
        "/analyze-company",
        json={"ticker": "INVALID_TICKER"},
    )

    assert response.status_code == 422
