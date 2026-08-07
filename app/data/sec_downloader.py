"""
SEC filing downloader.
"""

from __future__ import annotations

import requests

from app.data.sec_document import SECDocument


class SECDownloader:

    HEADERS = {
        "User-Agent": "AIFinancialAnalyst research@example.com"
    }

    def download(
        self,
        url: str,
    ) -> SECDocument:

        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        return SECDocument(
            url=url,
            html=response.text,
        )