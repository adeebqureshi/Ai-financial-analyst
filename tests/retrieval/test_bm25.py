from app.retrieval.bm25_index import BM25Index


def test_bm25_search():

    ids = [
        "1",
        "2",
        "3",
    ]

    docs = [
        "Apple revenue increased significantly.",
        "Microsoft cloud revenue grew.",
        "Tesla delivered more vehicles.",
    ]

    index = BM25Index()

    index.build(
        ids,
        docs,
    )

    results = index.search(
        "Apple revenue",
        top_k=1,
    )

    assert results == ["1"]


def test_invalid_build():

    index = BM25Index()

    try:

        index.build(
            ["1"],
            ["A", "B"],
        )

    except ValueError:

        assert True

    else:

        assert False