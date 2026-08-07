from app.data.filing import Filing


def test_filing():

    filing = Filing(
        accession_number="0000320193-24-000001",
        filing_type="10-K",
        company="Apple Inc.",
        filing_date="2025-09-30",
        url="https://www.sec.gov",
    )

    assert filing.filing_type == "10-K"

    assert filing.company == "Apple Inc."