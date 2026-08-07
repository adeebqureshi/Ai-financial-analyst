from app.data.sec_filings import SECFiling


def test_filing():

    filing = SECFiling(
        accession_number="000032019324000001",
        form="10-K",
        filing_date="2025-09-30",
        primary_document="aapl10k.htm",
    )

    assert filing.form == "10-K"