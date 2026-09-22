from __future__ import annotations
import re
MAX_TICKER_LENGTH = 10
INVALID_TICKER_MESSAGE = "Invalid ticker symbol."
def _full_ticker_pattern() -> re.Pattern[str]:
    return re.compile(
        r"^[A-Z0-9]+(?:[.\-][A-Z0-9]+)*$"
    )
_VALID_TICKER_RE = _full_ticker_pattern()
def normalize_ticker(value: str) -> str:
    if not isinstance(value, str):
        raise ValueError(INVALID_TICKER_MESSAGE)
    ticker = value.strip().upper()
    if not ticker or len(ticker) > MAX_TICKER_LENGTH:
        raise ValueError(INVALID_TICKER_MESSAGE)
    if not _VALID_TICKER_RE.fullmatch(ticker):
        raise ValueError(INVALID_TICKER_MESSAGE)
    return ticker
def is_valid_ticker(value: str) -> bool:
    try:
        normalize_ticker(value)
    except ValueError:
        return False
    return True