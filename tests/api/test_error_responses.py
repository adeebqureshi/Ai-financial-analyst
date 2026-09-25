from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api import register_exception_handlers
from app.api.dependencies.services import get_report_service
from app.api.routers.report import router as report_router
from app.core.exceptions import FinancialAnalystError


class _UnexpectedService:
    def generate_ticker_report(self, *, ticker: str, query: str):
        raise RuntimeError(
            r"SECRET_INTERNAL_VALUE / C:\\private\\application\\secret.py:123"
        )


def test_unexpected_http_exception_is_safe_and_logged(caplog):
    app = FastAPI()

    @app.get("/unexpected")
    async def unexpected():
        raise RuntimeError(
            r"SECRET_INTERNAL_VALUE / C:\\private\\application\\secret.py:123"
        )

    register_exception_handlers(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/unexpected")

    assert response.status_code == 500
    assert response.json()["message"] == "An internal server error occurred."
    assert response.json()["errors"][0]["code"] == "INTERNAL_ERROR"
    assert "SECRET_INTERNAL_VALUE" not in response.text
    assert "C:\\private" not in response.text
    assert "secret.py" not in response.text
    assert "Traceback" not in response.text
    assert caplog.records


def test_report_endpoint_does_not_return_unexpected_exception_details():
    app = FastAPI()
    app.include_router(report_router)
    register_exception_handlers(app)
    app.dependency_overrides[get_report_service] = lambda: _UnexpectedService()

    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/report", json={"ticker": "AAPL"})

    assert response.status_code == 500
    assert response.json()["message"] == "An unexpected internal error occurred."
    assert response.json()["errors"][0]["code"] == "INTERNAL_SERVER_ERROR"
    for secret in ("SECRET_INTERNAL_VALUE", "C:\\private", "secret.py", "RuntimeError"):
        assert secret not in response.text


def test_intentional_domain_error_contract_is_preserved():
    app = FastAPI()

    @app.get("/domain-error")
    async def domain_error():
        raise FinancialAnalystError("Safe domain message", error_code="DOMAIN_ERROR")

    register_exception_handlers(app)
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/domain-error")

    assert response.status_code == 500
    assert response.json()["message"] == "Safe domain message"
    assert response.json()["errors"][0]["code"] == "DOMAIN_ERROR"

