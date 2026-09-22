from __future__ import annotations
from datetime import date
from typing import Any
from app.core.config import Settings
from app.core.logging import get_logger
from app.enums.filing_type import FilingType
from app.ingestion.services.sec_service import SECService
from app.models.filing import Filing
from app.utils.tickers import normalize_ticker
_demo_sec_service = None
def _get_demo_sec_service():
    global _demo_sec_service
    if _demo_sec_service is None:
        from app.demo.services.demo_sec_service import DemoSECService
        _demo_sec_service = DemoSECService()
    return _demo_sec_service
logger = get_logger(__name__)
class FilingService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if settings.is_demo_mode:
            self._sec = _get_demo_sec_service()
        else:
            self._sec = SECService()
    def get_latest_filings(
        self,
        ticker: str,
        filing_type: FilingType | str = FilingType.FORM_10K,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        ticker = normalize_ticker(ticker)
        form = filing_type.value if isinstance(filing_type, FilingType) else filing_type
        try:
            filings = self._sec.get_latest_filings(
                ticker=ticker,
                form=form,
                limit=limit,
            )
            return self._normalize_filings(filings)
        except Exception as exc:
            logger.warning(
                "Failed to retrieve filings for %s: %s",
                ticker,
                exc,
            )
            return []
    def get_filing_by_accession(
        self,
        ticker: str,
        accession_number: str,
    ) -> dict[str, Any] | None:
        ticker = normalize_ticker(ticker)
        filings = self.get_latest_filings(ticker, limit=100)
        for filing in filings:
            if filing.get("accession_number") == accession_number:
                return filing
        return None
    def get_filings_by_date_range(
        self,
        ticker: str,
        start_date: date,
        end_date: date,
        filing_type: FilingType | str | None = None,
    ) -> list[dict[str, Any]]:
        filings = self.get_latest_filings(ticker, limit=100)
        form = filing_type.value if isinstance(filing_type, FilingType) else filing_type
        filtered = []
        for filing in filings:
            filing_date = filing.get("filing_date")
            if isinstance(filing_date, str):
                filing_date = date.fromisoformat(filing_date)
            if start_date <= filing_date <= end_date:
                if form is None or filing.get("filing_type") == form:
                    filtered.append(filing)
        return filtered
    def _normalize_filings(self, filings: Any) -> list[dict[str, Any]]:
        normalized = []
        for filing in filings:
            if hasattr(filing, "model_dump"):
                filing_dict = filing.model_dump()
            elif hasattr(filing, "dict"):
                filing_dict = filing.dict()
            else:
                filing_dict = filing
            normalized.append({
                "accession_number": filing_dict.get("accession_number", ""),
                "filing_type": filing_dict.get("filing_type", ""),
                "filing_date": filing_dict.get("filing_date"),
                "report_period": filing_dict.get("report_period"),
                "source_url": filing_dict.get("source_url", ""),
                "local_path": str(filing_dict.get("local_path", "")),
                "checksum": filing_dict.get("checksum"),
                "parser_status": filing_dict.get("parser_status", "pending"),
                "embedding_status": filing_dict.get("embedding_status", "pending"),
                "indexing_status": filing_dict.get("indexing_status", "pending"),
            })
        return normalized