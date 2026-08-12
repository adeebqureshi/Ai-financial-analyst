"""
Document metadata models.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(slots=True)
class DocumentMetadata:
    """
    Metadata associated with a financial document.

    Bitemporal fields:
        valid_from: Earliest date the information was true/relevant in the
            real world (e.g. reporting period start). ``None`` = unbounded.
        valid_until: Last date the information was true/relevant (e.g.
            reporting period end). ``None`` = open-ended.
        transaction_time: Date the system ingested the document.
            ``None`` = unknown ingestion date.
        period_of_report: SEC "period of report" date (the date as of which
            the filing reports information) when available.
    """

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

    # ── Bitemporal metadata (Phase 5) ─────────────────────────────────
    valid_from: date | None = None
    valid_until: date | None = None
    transaction_time: date | None = None
    period_of_report: date | None = None
