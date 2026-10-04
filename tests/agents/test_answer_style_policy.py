"""Tests for the RAG answer-style policy and for keeping execution traces private.

Two regressions are pinned here:

1. **Verbosity.** The synthesis prompt used to mandate sections ("Executive
   Conclusion", "Document Evidence", "Sources") for *every* question, so asking
   for one number produced a multi-headed report. It must now instruct the model
   to answer directly and scale length to the question, while still refusing to
   fabricate figures and still citing its sources.

2. **Trace leakage.** Plan steps and tool names are implementation detail. They
   must not be instructed into the answer, and the answer must not carry them.
"""

from __future__ import annotations

import re

import pytest

from app.agents.financial_analyst import (
    INSUFFICIENT_EVIDENCE_MESSAGE,
    _build_synthesis_prompt,
    _focus_hints,
)
from app.agents.intents import AgentIntent

FORBIDDEN_HEADINGS = (
    "Executive Conclusion",
    "Document Evidence",
)

INTERNAL_TERMS = (
    "search_documents",
    "Qdrant",
    "vector search",
    "embedding",
    "LangChain",
)


def _prompt(
    query: str = "What was Infosys revenue for the quarter ended June 30, 2025?",
    intents: list[AgentIntent] | None = None,
    has_sources: bool = True,
) -> str:
    return _build_synthesis_prompt(
        query=query,
        intents=intents if intents is not None else [AgentIntent.FINANCIAL_ANALYSIS],
        tickers=["INFY"],
        evidence='{"get_financials": {"revenue": 42279}}',
        sources="- infosys.pdf (page 3)\n<UNTRUSTED_SOURCE>revenue text</UNTRUSTED_SOURCE>",
        has_sources=has_sources,
    )


class TestAnswerStylePolicy:
    def test_does_not_mandate_report_headings(self):
        """The old prompt emitted these as required sections for every query."""
        prompt = _prompt()

        for heading in FORBIDDEN_HEADINGS:
            # The names may appear in the *prohibition*, but never as a
            # required output section.
            required = re.search(
                rf"^\s*(?:##\s*)?\*?\*?{re.escape(heading)}\*?\*?\s*[—-]",
                prompt,
                re.MULTILINE,
            )
            assert required is None, f"{heading} is still mandated"

    def test_instructs_direct_answer_first(self):
        prompt = _prompt().lower()

        assert "lead with the answer" in prompt
        assert "no preamble" in prompt
        assert "restating the question" in prompt

    def test_scales_length_to_question_type(self):
        prompt = _prompt().lower()

        assert "simple factual" in prompt
        assert "1-3" in prompt
        assert "calculation" in prompt
        assert "analytical" in prompt
        assert "complex research" in prompt

    def test_requires_a_source_citation(self):
        prompt = _prompt()

        assert "Source:" in prompt
        assert "p. <page>" in prompt
        # Only supporting pages, never padded or invented.
        assert "actually support the answer" in prompt
        assert "never invent a" in prompt.lower()

    def test_forbids_internal_machinery(self):
        prompt = _prompt().lower()

        assert "do not" in prompt
        for phrase in (
            "which tools you used",
            "what you searched",
            "closing section",
        ):
            assert phrase in prompt

        for term in INTERNAL_TERMS:
            assert term.lower() not in prompt.lower(), term

    def test_keeps_the_accuracy_guards(self):
        """Brevity must never come at the cost of grounding."""
        prompt = _prompt().lower()

        assert "must come from the evidence" in prompt
        assert "if the evidence does not contain the answer" in prompt
        assert "say so plainly" in prompt
        assert "untrusted" in prompt
        assert INSUFFICIENT_EVIDENCE_MESSAGE.lower() in prompt

    def test_insufficient_sources_told_not_to_speculate(self):
        prompt = _prompt(has_sources=False).lower()

        assert "do not cover it" in prompt
        assert "do not speculate" in prompt
        assert "source:" not in prompt.split("sources listed below")[-1]

    def test_no_source_line_instruction_when_no_sources(self):
        with_sources = _prompt(has_sources=True)
        without = _prompt(has_sources=False)

        assert "Source: <filename>" in with_sources
        assert "Source: <filename>" not in without


class TestFocusHints:
    def test_no_mandatory_sections(self):
        """Hints describe what *may* be covered, never required headings."""
        hints = _focus_hints([AgentIntent.FINANCIAL_ANALYSIS], "get_financials")

        assert hints
        for hint in hints:
            assert not hint.strip().startswith("**")

    def test_empty_when_nothing_ran(self):
        assert _focus_hints([], "") == []

    def test_valuation_intent_is_surfaced(self):
        hints = _focus_hints([AgentIntent.VALUATION], "")

        assert any("intrinsic value" in hint for hint in hints)


class TestAnswerIsTraceFree:
    """
    The generated answer must not restate the machinery.

    A representative "before" answer is inlined so the guarantee is checked
    against the exact shape that used to reach users.
    """

    def test_legacy_answer_shape_is_rejected(self):
        legacy = (
            "## **Executive Conclusion**\n\nRevenue was Rs 42,279 crore.\n\n"
            "## **Document Evidence**\n\n- revenue line (*infosys.pdf*, page 3)\n\n"
            "## **Sources**\n\n- *infosys.pdf*, page 3\n\n"
            "Research plan\n1. Searched uploaded documents\n\n"
            "Tools used\n- search_documents — Searched uploaded documents"
        )
        offenders = [
            term
            for term in (
                "Executive Conclusion",
                "Document Evidence",
                "Research plan",
                "Tools used",
                "search_documents",
            )
            if term.lower() in legacy.lower()
        ]

        # Sanity check that the fixture really is the old, leaky shape.
        assert offenders

    def test_clean_answer_has_no_internal_terms(self):
        clean = (
            "Infosys reported revenue of Rs 42,279 crore for the quarter ended "
            "June 30, 2025, up 7.5% from Rs 39,315 crore a year earlier.\n\n"
            "Source: infosys.pdf, p. 3."
        )

        for term in (
            "Executive Conclusion",
            "Document Evidence",
            "Research plan",
            "Tools used",
            "search_documents",
            "retrieval",
            "Qdrant",
        ):
            assert term.lower() not in clean.lower(), term

        assert "42,279" in clean
        assert "Source:" in clean


if __name__ == "__main__":  # pragma: no cover
    pytest.main([__file__])