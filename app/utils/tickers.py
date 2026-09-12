"""
tickers.py

Canonical, centralized ticker validation for the AI Financial Analyst project.

Every ticker entry point — API request schemas, domain models, services,
market-data providers, clients and storage path construction — funnels through
:func:`normalize_ticker` so untrusted input is validated and normalized exactly
once, in one place, *before* it reaches a financial-data provider or any other
downstream operation.

The validator performs real validation, not merely uppercasing:

    - Rejects empty / whitespace-only values and normalizes surrounding space.
    - Normalizes case to uppercase.
    - Enforces a centralized maximum length (``MAX_TICKER_LENGTH``).
    - Admits only the narrow character set the project's financial providers
      actually support (letters/digits plus the ``.``/``-`` separators used for
      share classes such as ``BRK.B``), with no leading/trailing separator.
    - Rejects embedded whitespace, quotes, script/query/shell characters,
      path separators and control characters.

The module is intentionally framework-free (standard library only) so it can be
shared safely by schemas, services and the provider layer without importer
cycles, and raises a plain ``ValueError`` so Pydantic request validation maps it
to a normal HTTP 422 client error.
"""

from __future__ import annotations

import re

# The longest ticker the application's supported providers (Yahoo / FMP) can
# meaningfully address. Kept generous enough to cover real share-class symbols
# (e.g. ``BRK.B``) and longer instrument ids without accepting garbage.
MAX_TICKER_LENGTH = 10

INVALID_TICKER_MESSAGE = "Invalid ticker symbol."


def _full_ticker_pattern() -> re.Pattern[str]:
    """
    Build the compiled ticker pattern.

    Canonical shape: one or more letters/digits, optionally followed by one or
    more ``[-.]``-separated alphanumeric segments (e.g. ``BRK.B``, ``BRK-B``).
    Requiring separators to appear only *between* alphanumeric segments rejects
    leading/trailing/adjacent separators, plus embedded whitespace, quotes,
    ``;``, ``&``, ``?``, ``=``, ``<``, ``>``, path separators and control
    characters. The length is bounded separately by ``MAX_TICKER_LENGTH``.
    Fullmatch ensures the entire string conforms.
    """
    return re.compile(
        r"^[A-Z0-9]+(?:[.\-][A-Z0-9]+)*$"
    )


_VALID_TICKER_RE = _full_ticker_pattern()


def normalize_ticker(value: str) -> str:
    """
    Validate and normalize a single ticker symbol.

    Args:
        value: Untrusted ticker input (may include surrounding whitespace and
            any casing).

    Returns:
        The canonical uppercase ticker, e.g. ``"AAPL"`` from ``"  aapl  "``.

    Raises:
        ValueError: If ``value`` is empty, too long, or contains any character
            outside the supported set. The error message is concise and does
            not reflect the raw (potentially malicious) input back to callers.
    """
    if not isinstance(value, str):
        raise ValueError(INVALID_TICKER_MESSAGE)

    ticker = value.strip().upper()

    if not ticker or len(ticker) > MAX_TICKER_LENGTH:
        raise ValueError(INVALID_TICKER_MESSAGE)

    if not _VALID_TICKER_RE.fullmatch(ticker):
        raise ValueError(INVALID_TICKER_MESSAGE)

    return ticker


def is_valid_ticker(value: str) -> bool:
    """
    Return ``True`` when ``value`` is a ticker that :func:`normalize_ticker`
    accepts, ``False`` otherwise. Never raises.
    """
    try:
        normalize_ticker(value)
    except ValueError:
        return False
    return True