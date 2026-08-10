"""
companies.py

Shared company-name ↔ ticker resolution helpers.

Used by the planner (ticker detection in questions) and by the tool layer
(document retrieval filtering). Keeping the hints in one place guarantees the
agent and its tools agree on which company a name refers to, which is what
prevents an Apple question from surfacing Microsoft documents.
"""

from __future__ import annotations

import re

# Company name → ticker hints (mirrors the frontend hints).
TICKER_HINTS: list[tuple[str, str]] = [
    ("apple", "AAPL"),
    ("microsoft", "MSFT"),
    ("nvidia", "NVDA"),
    ("amd", "AMD"),
    ("tesla", "TSLA"),
    ("amazon", "AMZN"),
    ("google", "GOOGL"),
    ("alphabet", "GOOGL"),
    ("meta", "META"),
    ("netflix", "NFLX"),
    ("intel", "INTC"),
    ("oracle", "ORCL"),
    ("salesforce", "CRM"),
    ("palantir", "PLTR"),
    ("berkshire", "BRK"),
    ("coca-cola", "KO"),
    ("pepsi", "PEP"),
    ("jpmorgan", "JPM"),
    ("goldman", "GS"),
    ("bank of america", "BAC"),
]

_UPPERCASE_PATTERN = re.compile(r"\b([A-Z]{2,5})\b")

_EXCLUDED_WORDS = {
    "AI", "ETF", "SEC", "CEO", "CFO", "COO", "GDP", "IPO", "ROE", "ROA",
    "EPS", "FED", "USA", "PDF", "RAG", "API", "EV", "EBITDA", "IT", "US",
    "UK", "COVID", "10K", "10Q", "10-K", "DCF", "FY", "USD", "Q1", "Q2",
    "Q3", "Q4",
}


def detect_tickers(query: str) -> list[str]:
    """
    Extract ticker symbols from a natural-language query.
    """
    found: list[str] = []

    lower = query.lower()

    for name, ticker in TICKER_HINTS:
        if name in lower and ticker not in found:
            found.append(ticker)

    for match in _UPPERCASE_PATTERN.finditer(query):
        word = match.group(1)
        if word not in _EXCLUDED_WORDS and word not in found:
            found.append(word)

    return found


def company_names_for(ticker: str) -> set[str]:
    """
    Company names (lowercased) that map to ``ticker``.
    """
    ticker = ticker.upper()

    return {
        name
        for name, symbol in TICKER_HINTS
        if symbol == ticker
    }
