from datetime import date
from pathlib import Path

from pytest import raises

from app.enums.filing_type import FilingType
from app.enums.processing_status import ProcessingStatus
from app.models.filing import Filing


def test_filing():

    filing = Filing(
        ticker="AAPL",
        cik="320193",
        accession_number="0000320193-24-000123",
        filing_type=FilingType.FORM_10K,
        filing_date=date(2024, 10, 31),
        report_period=date(2024, 9, 30),
        source_url="https://www.sec.gov",
        local_path=Path("storage/raw/sec/AAPL/2024/10-K.html"),
    )

    assert filing.ticker == "AAPL"

    assert filing.parser_status == ProcessingStatus.PENDING
    assert filing.embedding_status == ProcessingStatus.PENDING
    assert filing.indexing_status == ProcessingStatus.PENDING


def test_invalid_cik():

    with raises(ValueError):

        Filing(
            ticker="AAPL",
            cik="ABC123",
            accession_number="0000320193-24-000123",
            filing_type=FilingType.FORM_10K,
            filing_date=date.today(),
            report_period=date.today(),
            source_url="https://www.sec.gov",
            local_path=Path("dummy"),
        )