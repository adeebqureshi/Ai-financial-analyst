"""
SEC EDGAR document loader.
"""

from __future__ import annotations

import re
from datetime import date, datetime, timezone
from pathlib import Path

import requests

from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata

# SEC filing documents embed machine-readable metadata at the top of the
# HTML (Rfile header comment / meta tags). These fields are the authoritative
# source for filing dates -- never inferred from "today".
_FILING_DATE_RE = re.compile(
    r"(?:filing-date|FILED AS OF DATE|FILING DATE)\s*[=:]\s*(\d{8})",
    re.IGNORECASE,
)

_PERIOD_OF_REPORT_RE = re.compile(
    r"(?:period-of-report|PERIOD OF REPORT)\s*[=:]\s*(\d{8})",
    re.IGNORECASE,
)

_FORM_TYPE_RE = re.compile(
    r"(?:form-type|FORM TYPE)\s*[=:]\s*([A-Z]{1,2}-?\d*[A-Z]?)\b",
    re.IGNORECASE,
)

_CIK_RE = re.compile(
    r"(?:cik)\s*[=:]\s*(\d{10})",
    re.IGNORECASE,
)


def _parse_sec_date(value: str | None) -> date | None:
    """
    Parse a raw SEC date value into a ``date``.

    SEC header metadata commonly uses ``YYYYMMDD`` (e.g. ``20240115``).
    ``None`` or empty values return ``None``; malformed values are logged and
    returned as ``None`` rather than crash ingestion.
    """
    if not value:
        return None

    digits = re.sub(r"\D", "", value)

    if len(digits) != 8:
        return None

    try:
        return date(
            year=int(digits[:4]),
            month=int(digits[4:6]),
            day=int(digits[6:8]),
        )
    except ValueError:
        return None


class SECLoader(DocumentLoader):
    """
    Downloads SEC filings from EDGAR.
    """

    USER_AGENT = (
        "AI Financial Analyst "
        "(research@example.com)"
    )

    def load(
        self,
        url: str,
    ) -> FinancialDocument:

        response = requests.get(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
            },
            timeout=30,
        )

        response.raise_for_status()

        html = response.text

        return FinancialDocument(
            text=html,
            metadata=_metadata_from_filing_html(
                html=html,
                url=url,
            ),
        )


def _metadata_from_filing_html(
    html: str,
    url: str,
) -> DocumentMetadata:
    """
    Derive document metadata from the SEC filing's embedded header metadata.

    Sources:
        - ``filing-date``      → ``filing_date`` (publication date).
        - ``period-of-report`` → ``period_of_report`` (reporting period as
          of date).
        - ``form-type``        → ``form_type``.
        - ``cik``              → ``cik``.

    Missing values are left as ``None`` -- dates are never fabricated.
    """
    text = html[:200_000]  # header is always at the top

    filing_date = _parse_sec_date(
        _first_match(_FILING_DATE_RE, text)
    )

    period_of_report = _parse_sec_date(
        _first_match(_PERIOD_OF_REPORT_RE, text)
    )

    form_type = _first_match(_FORM_TYPE_RE, text)

    cik = _first_match(_CIK_RE, text)

    metadata = DocumentMetadata(
        source="sec",
        filename=Path(url).name,
        mime_type="text/html",
        form_type=form_type,
        cik=cik,
        filing_date=(
            datetime.combine(filing_date, datetime.min.time(), tzinfo=timezone.utc)
            if filing_date
            else None
        ),
        period_of_report=period_of_report,
    )

    _apply_temporal_metadata(metadata)

    return metadata


def _apply_temporal_metadata(metadata: DocumentMetadata) -> None:
    """
    Populate the bitemporal fields for a loaded SEC filing.

    Semantics (per Phase 5 roadmap):
        - ``transaction_time`` = the actual ingestion timestamp -- when the
          system obtained the document. This is the date the system *knew*
          the information and is the primary guard against look-ahead bias.
        - ``valid_from``       = the period-of-report date when available.
          SEC filings report information *as of* the period of report; the
          information in the filing is not considered "true for the real
          world" before that date.
        - ``valid_until``      = left open-ended for filings (a fiscal year
          result does not "expire" in the real-world sense that would make
          it unusable later).

    Critically, ``transaction_time`` is the system ingestion time -- NOT the
    filing publication date. A 2023 annual filing ingested into the system in
    2024 must NOT be available to an as-of-January-2023 query.
    """
    metadata.transaction_time = date.today()

    if metadata.period_of_report is not None:
        metadata.valid_from = metadata.period_of_report

    # If no period-of-report is available, fall back to the filing date.
    # The filing date is still a real SEC-provided date (never fabricated)
    # and represents when the public knew the information.
    if metadata.valid_from is None and metadata.filing_date is not None:
        metadata.valid_from = metadata.filing_date.date()


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)

    if match is None:
        return None

    return match.group(1)