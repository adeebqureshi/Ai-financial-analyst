from types import SimpleNamespace

from app.reports.markdown_report import MarkdownReport


def test_markdown_report():

    result = {
        "company": SimpleNamespace(
            name="Apple Inc.",
            ticker="AAPL",
        ),
        "market": SimpleNamespace(
            current_price=200,
            currency="USD",
        ),
        "analysis": SimpleNamespace(
            intrinsic_value=250,
            upside=25,
            recommendation="BUY",
            health_score=95,
            health_rating="EXCELLENT",
            piotroski_score=9,
            altman_score=3.4,
            beneish_score=-2.3,
        ),
    }

    report = MarkdownReport.generate(result)

    assert report.title == "AAPL Financial Report"
    assert report.ticker == "AAPL"
    assert "Apple Inc." in report.content
    assert "BUY" in report.content