from app.agents.report import InvestmentReport


def test_report():

    report = InvestmentReport(
        company="Apple",
        title="Apple Investment Report",
        body="Revenue increased strongly.",
    )

    assert report.company == "Apple"

    assert report.word_count == 3