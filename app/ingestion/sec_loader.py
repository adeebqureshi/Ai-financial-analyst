from __future__ import annotations
import re
from datetime import date, datetime, timezone
from pathlib import Path
import requests
from app.ingestion.document import FinancialDocument
from app.ingestion.loader import DocumentLoader
from app.ingestion.metadata import DocumentMetadata
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
    text = html[:200_000]
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
    metadata.transaction_time = date.today()
    if metadata.period_of_report is not None:
        metadata.valid_from = metadata.period_of_report
    if metadata.valid_from is None and metadata.filing_date is not None:
        metadata.valid_from = metadata.filing_date.date()
def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    if match is None:
        return None
    return match.group(1)