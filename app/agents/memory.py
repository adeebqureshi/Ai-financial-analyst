"""
memory.py

Lightweight conversational context for the agent.

The REST chat contract is stateless, so follow-up context ("it", "them",
"this company") is resolved from a small store keyed by an optional
``session_id``. This is intentionally minimal — it is *not* a second memory
system; it only carries the tickers/entities from the previous turn.

Design Decisions:
    - **A cache, not the source of truth**: Persistent conversation state
      lives in the chat store (``app.chat.store`` — PostgreSQL/SQLite, with
      an optional Redis cache). ``ChatService`` hydrates this resolver from
      the store before every turn and persists every completed turn back, so
      this in-process store is only a bounded, per-worker cache. A cache miss
      or eviction is self-healing: the next turn is re-hydrated from the
      database, so restarts and multi-worker deployments never lose context.
    - **Owner-scoped keys**: Entries are keyed by ``(owner_id, session_id)``
      — the same pair the chat store uses — so two users reusing the same
      client-generated ``session_id`` can never read or overwrite each
      other's follow-up context.
    - **In-process, bounded**: Entries expire after ``_TTL_SECONDS`` and the
      store is capped so it cannot grow unboundedly.
    - **Pronoun resolution only**: We only resolve entity references; the
      planner still classifies each new message from scratch.
"""

from __future__ import annotations

import threading
import time
from typing import Any

from app.core.logging import get_logger

logger = get_logger(__name__)

_TTL_SECONDS = 60 * 60  # 1 hour
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

# Financial terms that reference the previous turn's subject even without a
# pronoun ("What is the revenue?", "How is the cash flow?", "What about debt?").
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
    """
    Tiny per-session context store used to resolve follow-up questions.
    """

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
        """Store the entities mentioned in the latest turn (owner-scoped)."""
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
                # Evict the oldest entry.
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
        """Return the previous turn's context, or ``None``."""
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
        """
        Merge tickers detected in the current query with entities from the
        previous turn when the query refers back to them ("compare it with...").
        """
        previous = self.recall(session_id, owner_id=owner_id)

        if previous is None:
            return detected

        previous_tickers = previous.get("tickers") or []

        if not previous_tickers:
            return detected

        text = f" {query.lower()} "

        if detected:
            # e.g. "compare it with Microsoft" — detected has MSFT, previous
            # has AAPL; merge in previous tickers referenced by pronouns.
            if any(marker in text for marker in _PRONOUN_MARKERS):
                merged = list(previous_tickers)
                for ticker in detected:
                    if ticker not in merged:
                        merged.append(ticker)
                return merged
            return detected

        # No ticker detected at all: inherit the previous subject when the
        # query clearly refers back to it — via a pronoun, a question opener,
        # or a financial keyword ("and it's valuation?", "what is the
        # revenue?"). A topic switch ("thank you", "what is 2+2?") gets no
        # inherited ticker so no tool runs needlessly.
        if _references_previous_subject(text):
            return list(previous_tickers)

        return detected


def _session_key(owner_id: str | None, session_id: str) -> tuple[str | None, str]:
    """
    Build the owner-scoped cache key.

    Mirrors the chat store's ``(owner_id, session_id)`` uniqueness so follow-up
    context can never leak across users even when they reuse a session id.
    """
    return (owner_id, session_id)


def _references_previous_subject(text: str) -> bool:
    """
    True when ``text`` (a space-padded lowercased query) points back to the
    subject of the previous turn rather than starting a brand-new topic.

    Only a pronoun or a financial keyword counts as a reference, so a topic
    switch ("What is the weather today?", "thank you") inherits nothing.
    """
    if any(marker in text for marker in _PRONOUN_MARKERS):
        return True

    return any(keyword in text for keyword in _FOLLOWUP_KEYWORDS)
