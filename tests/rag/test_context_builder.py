from app.rag.context_builder import ContextBuilder
from app.rag.embedding import Embedding
from app.rag.search_result import SearchResult


def test_builder():

    builder = ContextBuilder()

    results = [
        SearchResult(
            embedding=Embedding(
                text="Apple revenue",
                vector=[1],
            ),
            score=0.9,
        ),
        SearchResult(
            embedding=Embedding(
                text="Microsoft cloud",
                vector=[2],
            ),
            score=0.8,
        ),
    ]

    context = builder.build(results)

    assert context.chunk_count == 2

    assert "Apple revenue" in context.text

    assert "Microsoft cloud" in context.text


def test_duplicate_chunks():

    builder = ContextBuilder()

    results = [
        SearchResult(
            embedding=Embedding(
                text="Apple revenue",
                vector=[1],
            ),
            score=1.0,
        ),
        SearchResult(
            embedding=Embedding(
                text="Apple revenue",
                vector=[2],
            ),
            score=0.9,
        ),
    ]

    context = builder.build(results)

    assert context.chunk_count == 1