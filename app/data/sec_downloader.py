from __future__ import annotations

from app.data.sec_document import SECDocument
from app.data.sec_http import sec_http_get_text


class SECDownloader:
    """SEC filing downloader, rate limited by the centralized SEC gateway.

    This module performs no local HTTP call: every download goes through
    :mod:`app.data.sec_http`, so it is covered by the distributed SEC request
    limit (and by the gateway's host validation).
    """

    HEADERS = {
        "User-Agent": "AIFinancialAnalyst research@example.com"
    }

    def download(
        self,
        url: str,
    ) -> SECDocument:
        html = sec_http_get_text(
            url,
            headers=self.HEADERS,
        )

        return SECDocument(
            url=url,
            html=html,
        )
