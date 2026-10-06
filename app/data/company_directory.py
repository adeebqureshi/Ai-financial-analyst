"""Canonical company universe + search/resolution (part 1: registry)."""

from __future__ import annotations

from dataclasses import dataclass

__all__ = [
    "CompanyInfo",
    "COMPANIES",
    "COMPANY_BY_TICKER",
]


@dataclass(frozen=True, slots=True)
class CompanyInfo:
    """Canonical company entity the whole app operates on."""

    ticker: str
    name: str
    exchange: str | None = None
    aliases: tuple[str, ...] = ()


def _c(
    ticker: str, name: str, exchange: str | None = None, aliases: tuple[str, ...] = ()
) -> CompanyInfo:
    return CompanyInfo(ticker=ticker, name=name, exchange=exchange, aliases=aliases)


COMPANIES: tuple[CompanyInfo, ...] = (
    _c("AAPL", "Apple Inc.", "NASDAQ", ("Apple",)),
    _c("MSFT", "Microsoft Corporation", "NASDAQ", ("Microsoft",)),
    _c("NVDA", "NVIDIA Corporation", "NASDAQ", ("NVIDIA", "Nvidia")),
    _c("GOOGL", "Alphabet Inc.", "NASDAQ", ("Google", "Alphabet")),
    _c("GOOG", "Alphabet Inc.", "NASDAQ", ("Google", "Alphabet")),
    _c("AMZN", "Amazon.com, Inc.", "NASDAQ", ("Amazon",)),
    _c("TSLA", "Tesla, Inc.", "NASDAQ", ("Tesla",)),
    _c("META", "Meta Platforms, Inc.", "NASDAQ", ("Meta", "Facebook")),
    _c("NFLX", "Netflix, Inc.", "NASDAQ", ("Netflix",)),
    _c("AMD", "Advanced Micro Devices, Inc.", "NASDAQ", ("AMD",)),
    _c("INTC", "Intel Corporation", "NASDAQ", ("Intel",)),
    _c("CRM", "Salesforce, Inc.", "NYSE", ("Salesforce",)),
    _c("ORCL", "Oracle Corporation", "NYSE", ("Oracle",)),
    _c("ADBE", "Adobe Inc.", "NASDAQ", ("Adobe",)),
    _c("AVGO", "Broadcom Inc.", "NASDAQ", ("Broadcom",)),
    _c("PLTR", "Palantir Technologies Inc.", "NASDAQ", ("Palantir",)),
    _c("COIN", "Coinbase Global, Inc.", "NASDAQ", ("Coinbase",)),
    _c("SHOP", "Shopify Inc.", "NYSE", ("Shopify",)),
    _c("SQ", "Block, Inc.", "NYSE", ("Block", "Square")),
    _c("PYPL", "PayPal Holdings, Inc.", "NASDAQ", ("PayPal",)),
    _c("SPOT", "Spotify Technology S.A.", "NYSE", ("Spotify",)),
    _c("ABNB", "Airbnb, Inc.", "NASDAQ", ("Airbnb",)),
    _c("UBER", "Uber Technologies, Inc.", "NYSE", ("Uber",)),
    _c("ARM", "Arm Holdings plc", "NASDAQ", ("Arm",)),
    _c("SMCI", "Super Micro Computer, Inc.", "NASDAQ", ("Super Micro",)),
    _c("AMAT", "Applied Materials, Inc.", "NASDAQ", ("Applied Materials",)),
    _c("MU", "Micron Technology, Inc.", "NASDAQ", ("Micron",)),
    _c("CSCO", "Cisco Systems, Inc.", "NASDAQ", ("Cisco",)),
    _c("JPM", "JPMorgan Chase & Co.", "NYSE", ("JPMorgan", "Chase")),
    _c("V", "Visa Inc.", "NYSE", ("Visa",)),
    _c("MA", "Mastercard Incorporated", "NYSE", ("Mastercard",)),
    _c("BAC", "Bank of America Corporation", "NYSE", ("Bank of America",)),
    _c("WFC", "Wells Fargo & Company", "NYSE", ("Wells Fargo",)),
    _c("GS", "The Goldman Sachs Group, Inc.", "NYSE", ("Goldman Sachs",)),
    _c("BRKB", "Berkshire Hathaway Inc.", "NYSE", ("Berkshire Hathaway",)),
    _c("WMT", "Walmart Inc.", "NYSE", ("Walmart",)),
    _c("COST", "Costco Wholesale Corporation", "NASDAQ", ("Costco",)),
    _c("KO", "The Coca-Cola Company", "NYSE", ("Coca-Cola", "Coca Cola")),
    _c("PEP", "PepsiCo, Inc.", "NASDAQ", ("PepsiCo", "Pepsi")),
    _c("DIS", "The Walt Disney Company", "NYSE", ("Disney",)),
    _c("BA", "The Boeing Company", "NYSE", ("Boeing",)),
    _c("XOM", "Exxon Mobil Corporation", "NYSE", ("ExxonMobil", "Exxon")),
    _c("PFE", "Pfizer Inc.", "NYSE", ("Pfizer",)),
    _c("JNJ", "Johnson & Johnson", "NYSE", ("Johnson & Johnson",)),
    _c("LLY", "Eli Lilly and Company", "NYSE", ("Eli Lilly", "Lilly")),
    _c("UNH", "UnitedHealth Group Incorporated", "NYSE", ("UnitedHealth",)),
    _c("T", "AT&T Inc.", "NYSE", ("AT&T", "ATT")),
    _c("NKE", "NIKE, Inc.", "NYSE", ("Nike",)),
    _c("MCD", "McDonald's Corporation", "NYSE", ("McDonald's", "McDonalds")),
    _c("SBUX", "Starbucks Corporation", "NASDAQ", ("Starbucks",)),
    _c("HD", "The Home Depot, Inc.", "NYSE", ("Home Depot",)),
    _c("CAT", "Caterpillar Inc.", "NYSE", ("Caterpillar",)),
    _c("GE", "GE Aerospace", "NYSE", ("GE", "General Electric")),
    _c("SAP", "SAP SE", "NYSE", ("SAP",)),
    _c("SNY", "Sanofi", "NASDAQ", ("Sanofi",)),
    _c("SNDK", "SanDisk Corporation", "NASDAQ", ("SanDisk", "Sandisk")),
)

COMPANY_BY_TICKER: dict[str, CompanyInfo] = {c.ticker: c for c in COMPANIES}
