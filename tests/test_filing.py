from datetime import date
from pathlib import Path

from app.enums.filing_type import FilingType
from app.models.filing import Filing


def test_filing():

    filing = Filing(
        ticker="AAPL",
        cik="320193",
        filing_type=FilingType.FORM_10K,
        filing_date=date(2024, 10, 31),
        report_period=date(2024, 9, 30),
        accession_number="0000320193-24-000123",
        local_path=Path("storage/raw/sec/AAPL/2024/10-K.html"),
        source_url="https://www.sec.gov",
    )

    assert filing.parsed is False
    assert filing.embedded is False