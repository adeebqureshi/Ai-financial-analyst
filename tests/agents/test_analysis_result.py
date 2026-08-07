from app.agents.analysis_result import AnalysisResult


def test_result():

    result = AnalysisResult(
        company="Apple",
        summary="Done",
        metrics={
            "ROE": 0.25,
            "ROA": 0.12,
        },
    )

    assert result.metric_count == 2

    assert result.company == "Apple"