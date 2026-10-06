"""API test for GET /companies/search (no network, no auth required)."""

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import register_exception_handlers
from app.api.routers.companies import router as companies_router


def _client() -> TestClient:
    app = FastAPI()
    app.include_router(companies_router)
    register_exception_handlers(app)
    return TestClient(app)


def test_companies_search_by_name() -> None:
    client = _client()
    response = client.get("/companies/search", params={"q": "Apple"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["results"][0]["ticker"] == "AAPL"


def test_companies_search_by_ticker_prefix() -> None:
    client = _client()
    response = client.get("/companies/search", params={"q": "NV"})
    assert response.status_code == 200
    tickers = [r["ticker"] for r in response.json()["data"]["results"]]
    assert "NVDA" in tickers


def test_companies_search_empty_query_returns_no_results() -> None:
    client = _client()
    response = client.get("/companies/search", params={"q": ""})
    assert response.status_code == 200
    assert response.json()["data"]["results"] == []
