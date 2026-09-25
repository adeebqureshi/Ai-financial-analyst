"""SECClient contract: every SEC request goes through the central gateway.

The client no longer performs its own HTTP call, so this test replaces the
transport on the centralized gateway and asserts that the SEC URL the client
uses was requested through it (and that the limiter was consulted).
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.data import sec_http
from app.data.sec_client import SECClient


def test_sec_client_uses_the_central_gateway(monkeypatch) -> None:
    response = MagicMock()
    response.json.return_value = {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."}
    }
    response.raise_for_status.return_value = None

    transport = MagicMock()
    transport.request.return_value = response

    gateway = sec_http.SECRequestGateway(
        limiter=MagicMock(),
        transport=transport,
        backoff_seconds=0.0,
    )
    monkeypatch.setattr(sec_http, "_shared_gateway", gateway)

    company = SECClient().company("AAPL")

    assert company.cik == "320193"
    assert company.ticker == "AAPL"
    assert "Apple" in company.title

    transport.request.assert_called_once()
    assert transport.request.call_args.args[1] == "https://www.sec.gov/files/company_tickers.json"
    gateway.limiter.acquire.assert_called_once()
