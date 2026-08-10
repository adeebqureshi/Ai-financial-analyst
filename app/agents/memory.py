"""
memory.py

Lightweight conversational context for the agent.

The REST chat contract is stateless, so follow-up context ("it", "them",
"this company") is resolved from an in-process store keyed by an optional
``session_id``. This is intentionally minimal — it is *not* a second memory
system; it only carries the tickers/entities from the previous turn.

Design Decisions:
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
    ) -> None:
        """Store the entities mentioned in the latest turn."""
        if not session_id:
            return

        entry: dict[str, Any] = {
            "tickers": list(tickers),
            "query": query,
            "answer": answer,
        }

        with self._lock:
            if len(self._store) >= _MAX_SESSIONS:
                # Evict the oldest entry.
                oldest = min(
                    self._store.keys(),
                    key=lambda key: self._store[key][0],
                )
                self._store.pop(oldest, None)

            self._store[session_id] = (time.monotonic(), entry)

    def recall(
        self,
        session_id: str | None,
    ) -> dict[str, Any] | None:
        """Return the previous turn's context, or ``None``."""
        if not session_id:
            return None

        with self._lock:
            entry = self._store.get(session_id)

            if entry is None:
                return None

            timestamp, data = entry

            if time.monotonic() - timestamp > _TTL_SECONDS:
                self._store.pop(session_id, None)
                return None

            return data

    def resolve_tickers(
        self,
        query: str,
        detected: list[str],
        session_id: str | None,
    ) -> list[str]:
        """
        Merge tickers detected in the current query with entities from the
        previous turn when the query refers back to them ("compare it with...").
        """
        previous = self.recall(session_id)

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

        # No ticker detected at all and the query refers back to the previous
        # subject ("and it's valuation?", "is it undervalued?").
        if any(marker in text for marker in _PRONOUN_MARKERS):
            return list(previous_tickers)

        return detected
