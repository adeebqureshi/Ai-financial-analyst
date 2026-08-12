"""
temporal_metadata.py

Bitemporal metadata model for the RAG system.

Two independent temporal dimensions are tracked for every document/chunk:

    valid_time
        = when the information was true/relevant in the real world
        (``valid_from`` / ``valid_until``)

    transaction_time
        = when the system actually obtained/ingested the information
        (``transaction_time``)

The central invariant for historical "as-of" queries is:

    For query date D, information is usable only when:

        transaction_time <= D          (the system knew it by D)
        AND valid_from     <= D        (it was true/relevant by D)
        AND (valid_until is None OR valid_until >= D)   (it had not expired by D)

This prevents look-ahead bias: a 2023 annual filing ingested in 2024 must NOT
be available to an "as of January 2023" query, even though it describes FY2023.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


def _coerce_date(value: Any) -> date | None:
    """
    Coerce a value to a ``date``.

    Accepts ``date``, ``datetime`` (truncated to date), ISO-8601 strings
    (``YYYY-MM-DD`` or full timestamps), and ``None``. Raises ``ValueError``
    for anything else so callers fail loudly rather than silently dropping
    temporal constraints.
    """
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    if isinstance(value, str):
        text = value.strip()

        if not text:
            return None

        # Try full ISO timestamp first, then plain date.
        try:
            return datetime.fromisoformat(text).date()
        except ValueError:
            pass

        try:
            return date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError(
                f"Cannot parse temporal date from {value!r}; "
                "expected YYYY-MM-DD or an ISO-8601 timestamp."
            ) from exc

    raise ValueError(
        f"Cannot coerce {type(value).__name__} to a date: {value!r}"
    )


@dataclass(slots=True, frozen=True)
class TemporalMetadata:
    """
    Bitemporal metadata attached to a document or chunk.

    Attributes:
        valid_from: Earliest date the information was true/relevant in the
            real world (inclusive). ``None`` means "unknown / not bounded".
        valid_until: Last date the information was true/relevant in the real
            world (inclusive). ``None`` means "open-ended / still valid".
        transaction_time: Date the system ingested/obtained the information.
            ``None`` means "unknown ingestion date".
    """

    valid_from: date | None = None
    valid_until: date | None = None
    transaction_time: date | None = None

    # ──────────────────────────────────────────────────────────────────
    # Construction helpers
    # ──────────────────────────────────────────────────────────────────

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TemporalMetadata":
        """
        Build from a payload dict (e.g. a Qdrant payload).

        Missing keys are treated as ``None``. Values may be ``date``,
        ``datetime`` or ISO-8601 strings.
        """
        if not data:
            return cls()

        return cls(
            valid_from=_coerce_date(data.get("valid_from")),
            valid_until=_coerce_date(data.get("valid_until")),
            transaction_time=_coerce_date(data.get("transaction_time")),
        )

    @classmethod
    def from_iso_strings(
        cls,
        valid_from: str | None = None,
        valid_until: str | None = None,
        transaction_time: str | None = None,
    ) -> "TemporalMetadata":
        """Build from ISO-8601 strings (used by serialization boundaries)."""
        return cls(
            valid_from=_coerce_date(valid_from),
            valid_until=_coerce_date(valid_until),
            transaction_time=_coerce_date(transaction_time),
        )

    # ──────────────────────────────────────────────────────────────────
    # Serialization
    # ──────────────────────────────────────────────────────────────────

    def to_dict(self) -> dict[str, str | None]:
        """
        Serialize to a JSON/Qdrant-safe dict with ISO-8601 date strings.

        ``None`` values are preserved as ``None`` so downstream consumers can
        distinguish "missing" from "open-ended".
        """
        return {
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "transaction_time": (
                self.transaction_time.isoformat()
                if self.transaction_time
                else None
            ),
        }

    # ──────────────────────────────────────────────────────────────────
    # Temporal predicates
    # ──────────────────────────────────────────────────────────────────

    def is_valid_at(self, query_date: date) -> bool:
        """
        True when this information was valid and known at ``query_date``.

        Conceptually:

            transaction_time <= query_date
            AND valid_from <= query_date
            AND (valid_until is None OR valid_until >= query_date)

        Missing temporal metadata is handled conservatively for historical
        queries: if ``transaction_time`` is missing we cannot prove the
        information was known by ``query_date``, so the chunk is excluded.
        This prevents look-ahead leakage at the cost of recall.
        """
        if self.transaction_time is not None:
            if self.transaction_time > query_date:
                return False
        else:
            # Missing transaction time: we cannot prove the system knew this
            # information by the query date. Conservative exclusion prevents
            # look-ahead leakage for historical queries.
            return False

        if self.valid_from is not None:
            if self.valid_from > query_date:
                return False

        if self.valid_until is not None:
            if self.valid_until < query_date:
                return False

        return True

    def is_known_by(self, query_date: date) -> bool:
        """
        True when the system had ingested this information by ``query_date``.

        This is the transaction-time-only check (no valid-time constraints).
        """
        if self.transaction_time is None:
            return False

        return self.transaction_time <= query_date

    def is_valid_during(self, query_date: date) -> bool:
        """
        True when the information was true/relevant in the real world at
        ``query_date`` (valid-time-only check, no transaction-time constraint).
        """
        if self.valid_from is not None and self.valid_from > query_date:
            return False

        if self.valid_until is not None and self.valid_until < query_date:
            return False

        return True

    @property
    def has_temporal_metadata(self) -> bool:
        """True when at least one temporal field is set."""
        return any(
            value is not None
            for value in (
                self.valid_from,
                self.valid_until,
                self.transaction_time,
            )
        )

    def __str__(self) -> str:
        return (
            f"TemporalMetadata(valid_from={self.valid_from}, "
            f"valid_until={self.valid_until}, "
            f"transaction_time={self.transaction_time})"
        )