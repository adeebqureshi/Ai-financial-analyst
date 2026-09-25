from __future__ import annotations

from app.data.sec_company import SECCompany
from app.data.sec_http import sec_http_get_json
from app.utils.tickers import normalize_ticker


class SECClient:
    """SEC company lookup, rate limited by the centralized SEC gateway.

    This module performs no local HTTP call: every request goes through
    :mod:`app.data.sec_http`, which enforces the distributed SEC limit of
    10 requests per rolling second.
    """

    BASE_URL = "https://www.sec.gov"
    COMPANY_TICKERS_URL = f"{BASE_URL}/files/company_tickers.json"

    HEADERS = {
        "User-Agent": (
            "AIFinancialAnalyst "
            "research@example.com"
        )
    }

    def company(
        self,
        ticker: str,
    ) -> SECCompany:
        companies = sec_http_get_json(
            self.COMPANY_TICKERS_URL,
            headers=self.HEADERS,
        )

        ticker = normalize_ticker(ticker)

        for company in companies.values():
            if company["ticker"] == ticker:
                return SECCompany(
                    cik=str(company["cik_str"]),
                    ticker=company["ticker"],
                    title=company["title"],
                )

        raise ValueError(
            f"{ticker} not found."
        )
