from __future__ import annotations
import threading
import time
from typing import Any
from app.core.logging import get_logger
logger = get_logger(__name__)
_TTL_SECONDS = 60 * 60
_MAX_SESSIONS = 256
_PRONOUN_MARKERS = (
    " it ",
    " them ",
    " this company ",
    " that company ",
    " these companies ",
    " those companies ",
    " the first ",
    " the second ",
    " first company ",
    " second company ",
    " which one ",
    " which company ",
    " which stock ",
    " one of them ",
    " both companies ",
)
_FOLLOWUP_KEYWORDS = (
    "valuation",
    "price",
    "revenue",
    "earnings",
    "income",
    "risk",
    "health",
    "financials",
    "margin",
    "growth",
    "profitability",
    "ratio",
    "dcf",
    "intrinsic",
    "undervalued",
    "overvalued",
    "dividend",
    "stock",
    "share",
    "buy",
    "sell",
    "recommend",
    "investment",
    "thesis",
    "report",
    "performance",
    "cash flow",
    "balance sheet",
    "income statement",
    "debt",
    "liquidity",
    "solvency",
    "asset",
    "liabilit",
)
class ConversationMemory:
    def __init__(self) -> None:
        self._store: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()
    def remember(
        self,
        session_id: str,
        tickers: list[str],
        query: str,
        answer: str,
        *,
        owner_id: str | None = None,
    ) -> None:
        if not session_id:
            return
        entry: dict[str, Any] = {
            "tickers": list(tickers),
            "query": query,
            "answer": answer,
        }
        key = _session_key(owner_id, session_id)
        with self._lock:
            if len(self._store) >= _MAX_SESSIONS:
                oldest = min(
                    self._store.keys(),
                    key=lambda key: self._store[key][0],
                )
                self._store.pop(oldest, None)
            self._store[key] = (time.monotonic(), entry)
    def recall(
        self,
        session_id: str | None,
        *,
        owner_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not session_id:
            return None
        key = _session_key(owner_id, session_id)
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            timestamp, data = entry
            if time.monotonic() - timestamp > _TTL_SECONDS:
                self._store.pop(key, None)
                return None
            return data
    def resolve_tickers(
        self,
        query: str,
        detected: list[str],
        session_id: str | None,
        *,
        owner_id: str | None = None,
    ) -> list[str]:
        previous = self.recall(session_id, owner_id=owner_id)
        if previous is None:
            return detected
        previous_tickers = previous.get("tickers") or []
        if not previous_tickers:
            return detected
        text = f" {query.lower()} "
        if detected:
            if any(marker in text for marker in _PRONOUN_MARKERS):
                merged = list(previous_tickers)
                for ticker in detected:
                    if ticker not in merged:
                        merged.append(ticker)
                return merged
            return detected
        if _references_previous_subject(text):
            return list(previous_tickers)
        return detected
def _session_key(owner_id: str | None, session_id: str) -> tuple[str | None, str]:
    return (owner_id, session_id)
def _references_previous_subject(text: str) -> bool:
    if any(marker in text for marker in _PRONOUN_MARKERS):
        return True
    return any(keyword in text for keyword in _FOLLOWUP_KEYWORDS)