from app.rag.reranker import RuleBasedCrossEncoder


def test_encoder():

    encoder = RuleBasedCrossEncoder()

    score = encoder.score(
        "apple revenue",
        "apple revenue increased",
    )

    assert score == 2.0