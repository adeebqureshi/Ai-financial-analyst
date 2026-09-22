from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime
@dataclass(slots=True)
class DocumentMetadata:
    source: str
    filename: str
    company: str | None = None
    cik: str | None = None
    form_type: str | None = None
    filing_date: datetime | None = None
    language: str = "en"
    mime_type: str | None = None
    checksum: str | None = None
    extra: dict[str, str] = field(default_factory=dict)
    valid_from: date | None = None
    valid_until: date | None = None
    transaction_time: date | None = None
    period_of_report: date | None = None