from app.retrieval.bm25_index import BM25Index
def _build_index() -> BM25Index:
    index = BM25Index()
    index.build(
        ids=["doc-a:000000", "doc-a:000001", "doc-b:000000"],
        documents=[
            "apple revenue grew strongly in fiscal 2024",
            "apple supply chain risk from tariffs",
            "alice private notes revenue tariff details",
        ],
        owner_ids=["user-a", "user-a", "user-b"],
    )
    return index
def test_bm25_owner_filter_excludes_foreign_chunks():
    index = _build_index()
    results = index.search("revenue tariff", top_k=3, owner_id="user-a")
    assert results == ["doc-a:000000", "doc-a:000001"]
def test_bm25_owner_filter_never_returns_foreign_ids():
    index = _build_index()
    results = index.search("revenue tariff details", top_k=5, owner_id="user-a")
    assert all(doc_id.startswith("doc-a:") for doc_id in results)
    assert "doc-b:000000" not in results
def test_bm25_without_owner_keeps_all_results():
    index = _build_index()
    results = index.search("revenue tariff", top_k=3)
    assert len(results) == 3
def test_bm25_build_rejects_mismatched_owner_ids():
    index = BM25Index()
    try:
        index.build(
            ids=["a", "b"],
            documents=["text one", "text two"],
            owner_ids=["user-a"],
        )
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError for mismatched owner_ids")