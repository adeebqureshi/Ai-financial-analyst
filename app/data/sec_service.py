"""
SEC service.
"""

from __future__ import annotations

from bs4 import BeautifulSoup

from app.data.sec_document import SECDocument


class SECService:

    def extract_text(
        self,
        document: SECDocument,
    ) -> str:

        soup = BeautifulSoup(
            document.html,
            "html.parser",
        )

        return soup.get_text(
            separator=" ",
            strip=True,
        )