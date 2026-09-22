from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any
def _coerce_date(value: Any) -> date | None:
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
    valid_from: date | None = None
    valid_until: date | None = None
    transaction_time: date | None = None
    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "TemporalMetadata":
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
        return cls(
            valid_from=_coerce_date(valid_from),
            valid_until=_coerce_date(valid_until),
            transaction_time=_coerce_date(transaction_time),
        )
    def to_dict(self) -> dict[str, str | None]:
        return {
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "transaction_time": (
                self.transaction_time.isoformat()
                if self.transaction_time
                else None
            ),
        }
    def is_valid_at(self, query_date: date) -> bool:
        if self.transaction_time is not None:
            if self.transaction_time > query_date:
                return False
        else:
            return False
        if self.valid_from is not None:
            if self.valid_from > query_date:
                return False
        if self.valid_until is not None:
            if self.valid_until < query_date:
                return False
        return True
    def is_known_by(self, query_date: date) -> bool:
        if self.transaction_time is None:
            return False
        return self.transaction_time <= query_date
    def is_valid_during(self, query_date: date) -> bool:
        if self.valid_from is not None and self.valid_from > query_date:
            return False
        if self.valid_until is not None and self.valid_until < query_date:
            return False
        return True
    @property
    def has_temporal_metadata(self) -> bool:
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