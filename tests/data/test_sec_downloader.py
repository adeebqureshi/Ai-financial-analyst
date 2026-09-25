"""SECDownloader contract: every SEC request goes through the central gateway."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.data import sec_http
from app.data.sec_downloader import SECDownloader


def test_downloader_uses_the_central_gateway(monkeypatch) -> None:
    response = MagicMock()
    response.text = "<html><body>Apple Inc. 10-K</body></html>"
    response.raise_for_status.return_value = None

    transport = MagicMock()
    transport.request.return_value = response

    gateway = sec_http.SECRequestGateway(
        limiter=MagicMock(),
        transport=transport,
        backoff_seconds=0.0,
    )
    monkeypatch.setattr(sec_http, "_shared_gateway", gateway)

    url = "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl.htm"
    document = SECDownloader().download(url)

    assert document.length > 0
    assert document.url == url

    transport.request.assert_called_once()
    assert transport.request.call_args.args[1] == url
    assert (
        transport.request.call_args.kwargs["headers"]["User-Agent"]
        == SECDownloader.HEADERS["User-Agent"]
    )
    gateway.limiter.acquire.assert_called_once()
