"""SECLoader contract: filing HTML is fetched through the central gateway.

The loader used to call ``requests.get`` directly; it now delegates to the
centralized SEC gateway, which owns the distributed rate limit and the SEC
identification headers.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.data import sec_http
from app.ingestion.sec_loader import SECLoader

_FILING_HTML = (
    "<html><body>"
    "<div>FILED AS OF DATE: 20240928</div>"
    "<div>PERIOD OF REPORT: 20240928</div>"
    "<div>CIK: 0000320193</div>"
    "<p>Apple 10-K</p>"
    "</body></html>"
)


def test_sec_loader_uses_the_central_gateway(monkeypatch) -> None:
    response = MagicMock()
    response.text = _FILING_HTML
    response.raise_for_status.return_value = None

    transport = MagicMock()
    transport.request.return_value = response

    gateway = sec_http.SECRequestGateway(
        limiter=MagicMock(),
        transport=transport,
        backoff_seconds=0.0,
    )
    monkeypatch.setattr(sec_http, "_shared_gateway", gateway)

    loader = SECLoader()
    document = loader.load("https://www.sec.gov/test.html")

    assert document.metadata.source == "sec"
    assert "Apple" in document.text

    transport.request.assert_called_once()
    assert transport.request.call_args.args[1] == "https://www.sec.gov/test.html"
    assert (
        transport.request.call_args.kwargs["headers"]["User-Agent"] == SECLoader.USER_AGENT
    )
    gateway.limiter.acquire.assert_called_once()
