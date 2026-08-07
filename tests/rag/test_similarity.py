from app.rag.similarity import CosineSimilarity


def test_similarity():

    score = CosineSimilarity.compute(
        [1, 0],
        [1, 0],
    )

    assert score == 1.0


def test_orthogonal():

    score = CosineSimilarity.compute(
        [1, 0],
        [0, 1],
    )

    assert score == 0.0