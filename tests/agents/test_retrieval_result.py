from app.agents.retrieval_result import RetrievalResult


def test_result():

    result = RetrievalResult(
        query="Apple",
        documents=[
            "Doc 1",
            "Doc 2",
        ],
    )

    assert result.count == 2