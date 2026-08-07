from app.agents.analysis_result import AnalysisResult
from app.agents.report_writer import ReportWriterAgent
from app.agents.retrieval_result import RetrievalResult


def test_writer():

    writer = ReportWriterAgent()

    retrieval = RetrievalResult(
        query="Apple",
        documents=[
            "Doc 1",
            "Doc 2",
        ],
    )

    analysis = AnalysisResult(
        company="Apple",
        summary="Financial analysis completed.",
        metrics={
            "ROE": 0.25,
            "ROA": 0.15,
        },
    )

    report = writer.write(
        retrieval,
        analysis,
    )

    assert report.company == "Apple"

    assert "Financial analysis completed." in report.body

    assert report.title == "Apple Investment Report"