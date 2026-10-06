"""Tests for the canonical company directory + resolver (no network)."""

import pytest

from app.data.company_directory import COMPANIES, COMPANY_BY_TICKER
from app.data.company_search import resolve_company, search_companies


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("AAPL", "AAPL"),
        ("aapl", "AAPL"),
        (" Apple ", "AAPL"),
        ("Apple", "AAPL"),
        ("apple", "AAPL"),
        ("Apple Inc.", "AAPL"),
        ("NVDA", "NVDA"),
        ("nvda", "NVDA"),
        ("NVIDIA", "NVDA"),
        ("nvidia", "NVDA"),
        ("NVIDIA Corporation", "NVDA"),
        ("MSFT", "MSFT"),
        ("microsoft", "MSFT"),
        ("AMZN", "AMZN"),
        ("amazon", "AMZN"),
        ("TSLA", "TSLA"),
        ("tesla", "TSLA"),
        ("GOOGL", "GOOGL"),
        ("Google", "GOOGL"),
        ("CRM", "CRM"),
        ("Salesforce", "CRM"),
        ("SAP", "SAP"),
        ("SNY", "SNY"),
        ("Sanofi", "SNY"),
        ("SNDK", "SNDK"),
        ("SanDisk", "SNDK"),
    ],
)
def test_resolve_company_canonical(raw: str, expected: str) -> None:
    company = resolve_company(raw)
    assert company is not None
    assert company.ticker == expected


def test_apple_and_aapl_resolve_identically() -> None:
    assert resolve_company("Apple") == resolve_company("AAPL")
    assert resolve_company("Apple") is not None
    assert resolve_company("Apple").ticker == "AAPL"  # type: ignore[union-attr]


def test_nvidia_and_nvda_resolve_identically() -> None:
    assert resolve_company("NVIDIA") == resolve_company("NVDA")
    assert resolve_company("NVIDIA") is not None
    assert resolve_company("NVIDIA").ticker == "NVDA"  # type: ignore[union-attr]


@pytest.mark.parametrize("raw", ["", "   ", "not a real company xyz", None])
def test_resolve_company_unknown_returns_none(raw: str | None) -> None:
    assert resolve_company(raw) is None


def test_search_prefix_narrows() -> None:
    one = {c.ticker for c in search_companies("S", limit=50)}
    two = {c.ticker for c in search_companies("SA")}
    three = {c.ticker for c in search_companies("SAN")}
    assert "CRM" in one
    assert len(one) >= len(two)
    assert {"CRM", "SAP"} <= two
    assert {"SNDK", "SNY"} <= three


@pytest.mark.parametrize(
    "query,expected",
    [
        ("AAP", "AAPL"),
        ("aapl", "AAPL"),
        ("app", "AAPL"),
        ("apple", "AAPL"),
        ("nvi", "NVDA"),
        ("tes", "TSLA"),
        ("TSL", "TSLA"),
    ],
)
def test_search_matching(query: str, expected: str) -> None:
    assert search_companies(query)[0].ticker == expected


def test_directory_has_no_duplicates_and_uppercase_tickers() -> None:
    tickers = [c.ticker for c in COMPANIES]
    assert len(tickers) == len(set(tickers)) == len(COMPANY_BY_TICKER)
    assert all(t == t.upper() for t in tickers)
