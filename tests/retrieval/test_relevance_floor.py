from __future__ import annotations

import pytest

from app.retrieval.models import RetrievedChunk
from app.retrieval.retrieval_engine import RetrievalEngine


def _chunk(chunk_id: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=chunk_id,
        chunk_id=chunk_id,
        text=f"text for {chunk_id}",
        score=0.0,
        document_id="doc-1",
        filename="report.pdf",
        page=1,
        ticker="",
        filing_type="",
        filing_date=None,
        section="",
        source="",
    )


def _engine(floor: float) -> RetrievalEngine:
    engine = RetrievalEngine.__new__(RetrievalEngine)
    engine._min_similarity = floor
    engine._last_dropped = 0
    return engine


class TestRelevanceFloor:

    def test_unrelated_chunks_are_dropped(self) -> None:
        engine = _engine(0.30)
        chunks = [_chunk("a"), _chunk("b")]
        similarity = {"a": 0.05, "b": 0.11}

        kept = engine._apply_relevance_floor(chunks, similarity)

        assert kept == []
        assert engine._last_dropped == 2

    def test_relevant_chunks_are_kept(self) -> None:
        engine = _engine(0.30)
        chunks = [_chunk("a")]
        similarity = {"a": 0.62}

        kept = engine._apply_relevance_floor(chunks, similarity)

        assert [c.id for c in kept] == ["a"]
        assert engine._last_dropped == 0

    def test_only_the_irrelevant_chunks_are_dropped(self) -> None:
        engine = _engine(0.30)
        chunks = [_chunk("keep"), _chunk("drop")]
        similarity = {"keep": 0.60, "drop": 0.04}

        kept = engine._apply_relevance_floor(chunks, similarity)

        assert [c.id for c in kept] == ["keep"]
        assert engine._last_dropped == 1

    def test_chunk_without_a_measured_similarity_is_kept(self) -> None:
        engine = _engine(0.30)
        chunks = [_chunk("bm25-only")]

        kept = engine._apply_relevance_floor(chunks, {})

        assert [c.id for c in kept] == ["bm25-only"]

    def test_non_numeric_similarity_is_kept(self) -> None:
        engine = _engine(0.30)
        chunks = [_chunk("a")]

        kept = engine._apply_relevance_floor(chunks, {"a": "not-a-number"})

        assert [c.id for c in kept] == ["a"]
        assert engine._last_dropped == 0

    def test_boolean_similarity_is_ignored(self) -> None:
        engine = _engine(0.30)
        chunks = [_chunk("a")]

        kept = engine._apply_relevance_floor(chunks, {"a": False})

        assert [c.id for c in kept] == ["a"]

    def test_floor_of_zero_disables_the_guard(self) -> None:
        engine = _engine(0.0)
        chunks = [_chunk("a"), _chunk("b")]

        kept = engine._apply_relevance_floor(chunks, {"a": 0.0, "b": 0.0})

        assert [c.id for c in kept] == ["a", "b"]
        assert engine._last_dropped == 0

    def test_empty_retrieval_is_unchanged(self) -> None:
        engine = _engine(0.30)
        assert engine._apply_relevance_floor([], {}) == []

    def test_floor_matches_chunk_id_when_id_differs(self) -> None:
        engine = _engine(0.30)
        chunk = _chunk("row-id")
        chunk.id = "row-id"

        kept = engine._apply_relevance_floor([chunk], {"row-id": 0.05})

        assert kept == []
        assert engine._last_dropped == 1
