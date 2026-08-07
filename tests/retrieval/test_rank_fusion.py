from app.retrieval.rank_fusion import RankFusion


def test_rrf():

    fusion = RankFusion()

    dense = [
        "A",
        "B",
        "C",
    ]

    sparse = [
        "B",
        "A",
        "D",
    ]

    results = fusion.fuse(
        dense,
        sparse,
    )

    assert "A" in results
    assert "B" in results
    assert "C" in results
    assert "D" in results

    assert len(results) == 4