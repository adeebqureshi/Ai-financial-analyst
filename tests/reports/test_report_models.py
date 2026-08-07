from app.reports.report_models import Report


def test_report():

    report = Report(
        title="Apple",
        ticker="AAPL",
        content="Hello",
    )

    assert report.title == "Apple"
    assert report.ticker == "AAPL"
    assert report.content == "Hello"