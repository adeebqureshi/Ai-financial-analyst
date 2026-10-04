"""Citation filtering for chat answers.

The answer names the pages it relied on (``Source: file.pdf, p. 3.``). The
messages endpoint uses those references to decide which retrieved chunks are
worth offering as citations, so that a one-page answer is not presented as if it
were drawn from every page the retriever happened to return.
"""

from __future__ import annotations

from app.services.chat_service import _build_citations, _cited_pages


def _chunk(page: int, filename: str = "Infosys Annual Report.pdf") -> dict:
    return {
        "document_id": "doc1",
        "filename": filename,
        "page": page,
        "chunk_id": f"doc1:{page}",
        "score": 0.9,
    }


class TestCitedPages:
    def test_single_page(self):
        assert _cited_pages("Answer.\n\nSource: Infosys AR.pdf, p. 3.") == {
            ("infosysar", 3)
        }

    def test_two_pages_with_and(self):
        cited = _cited_pages("Answer.\n\nSource: Infosys AR.pdf, p. 1 and p. 3.")

        assert cited == {("infosysar", 1), ("infosysar", 3)}

    def test_two_documents_in_one_line(self):
        cited = _cited_pages(
            "Answer.\n\nSource: a.pdf, p. 3; b.pdf, p. 4."
        )

        assert cited == {("a", 3), ("b", 4)}

    def test_page_range(self):
        cited = _cited_pages("Answer.\n\nSource: ar.pdf, pp. 3-5.")

        assert cited == {("ar", 3), ("ar", 4), ("ar", 5)}

    def test_markdown_emphasis_is_ignored(self):
        cited = _cited_pages(
            "Answer.\n\nSource: **Infosys** Annual Report*.pdf*, page 12."
        )

        assert cited == {("infosysannualreport", 12)}

    def test_no_citation_returns_none(self):
        """None means "fall back to retrieved chunks", not "cite nothing"."""
        assert _cited_pages("Just prose with no citation.") is None

    def test_empty_answer_returns_none(self):
        assert _cited_pages("") is None


class TestBuildCitations:
    def test_only_cited_pages_are_returned(self):
        chunks = [_chunk(1), _chunk(3), _chunk(4), _chunk(7)]

        citations = _build_citations(
            chunks, "Revenue was X.\n\nSource: Infosys Annual Report.pdf, p. 3."
        )

        assert [c.page for c in citations] == [3]

    def test_multiple_cited_pages_are_all_returned(self):
        chunks = [_chunk(1), _chunk(3), _chunk(7)]

        citations = _build_citations(
            chunks,
            "Answer.\n\nSource: Infosys Annual Report.pdf, p. 1 and p. 3.",
        )

        assert sorted(c.page for c in citations) == [1, 3]

    def test_falls_back_to_all_chunks_without_a_citation(self):
        chunks = [_chunk(1), _chunk(3)]

        citations = _build_citations(chunks, "No citation line here.")

        assert [c.page for c in citations] == [1, 3]

    def test_never_invents_a_page(self):
        """A cited page that was not retrieved must not appear as a citation."""
        chunks = [_chunk(3)]

        citations = _build_citations(
            chunks, "Answer.\n\nSource: Infosys Annual Report.pdf, p. 99."
        )

        assert citations == []

    def test_preserves_document_metadata(self):
        citations = _build_citations(
            [_chunk(3)], "Answer.\n\nSource: Infosys Annual Report.pdf, p. 3."
        )

        assert citations[0].filename == "Infosys Annual Report.pdf"
        assert citations[0].document_id == "doc1"
        assert citations[0].chunk_id == "doc1:3"

    def test_deduplicates_repeated_pages(self):
        citations = _build_citations(
            [_chunk(3), _chunk(3)],
            "Answer.\n\nSource: Infosys Annual Report.pdf, p. 3.",
        )

        assert len(citations) == 1

    def test_skips_chunks_without_a_document_id(self):
        orphan = {"filename": "x.pdf", "page": 3, "chunk_id": "c"}

        citations = _build_citations(
            [orphan, _chunk(3)], "Answer.\n\nSource: Infosys Annual Report.pdf, p. 3."
        )

        assert len(citations) == 1