"""
SEC EDGAR client.
"""

from __future__ import annotations

import requests

from app.data.sec_company import SECCompany


class SECClient:

    BASE_URL = "https://www.sec.gov"

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

        url = (
            "https://www.sec.gov/files/company_tickers.json"
        )

        response = requests.get(
            url,
            headers=self.HEADERS,
            timeout=30,
        )

        response.raise_for_status()

        companies = response.json()

        ticker = ticker.upper()

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