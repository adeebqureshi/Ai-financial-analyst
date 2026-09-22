from __future__ import annotations
from app.enums.exchange import Exchange
from app.models.company import Company
class CompanyMapper:
    @staticmethod
    def from_edgar(edgar_company) -> Company:
        ticker = "UNKNOWN"
        if getattr(edgar_company, "tickers", None):
            ticker = edgar_company.tickers[0]
        return Company(
            ticker=ticker,
            cik=str(edgar_company.cik),
            name=edgar_company.name,
            exchange=Exchange.NASDAQ,
            sector="Unknown",
            industry="Unknown",
            country="USA",
            currency="USD",
            website=None,
            market_cap=None,
        )