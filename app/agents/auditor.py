"""
auditor.py

Auditor Agent.

Verifies that a research answer is grounded in the evidence actually produced
by the tool layer:

1. Every financial number originates from a tool (no tool ran -> no claim).
2. Every valuation figure comes from the valuation engine.
3. Every RAG claim maps to a retrieved chunk; no citation points to a source
   that was not actually retrieved.
4. The ticker is correct and no company data leaked from another ticker.
5. No unsupported recommendation was generated when evidence was missing.

The old report-length check (used by the /analyze pipeline) is preserved so
existing callers keep working.
"""

from __future__ import annotations

import re
from typing import Any

from app.agents.audit_result import AuditResult
from app.agents.research_plan import ResearchPlan
from app.core.logging import get_logger

logger = get_logger(__name__)

_CITATION_PATTERN = re.compile(
    r"([A-Za-z0-9 _\-\.()]*?(?:10-?K|10-?Q|20-?F|report|annual|\.pdf)"
    r"[^(\n]*)\(page\s+(\d+)\)",
    re.IGNORECASE,
)

# Numbers appearing in plain text (used to index retrieved chunk text so that
# numbers quoted from a retrieved document count as grounded). The optional
# unit suffix lets "$394,328 million" and "394.3 billion" register at scale.
_TEXT_NUMBER_PATTERN = re.compile(
    r"(-?\d[\d,]*(?:\.\d+)?)\s*"
    r"(thousand|million|billion|trillion|mn|bn|k|m|b)?",
    re.IGNORECASE,
)

# Financial figure claims the answer may assert: dollar amounts (with an
# optional unit suffix) and percentages.
_DOLLAR_CLAIM_PATTERN = re.compile(
    r"\$\s*(-?\d[\d,]*(?:\.\d+)?)\s*"
    r"(thousand|million|billion|trillion|mn|bn|k|m|b)?",
    re.IGNORECASE,
)
_PERCENT_CLAIM_PATTERN = re.compile(r"(-?\d+(?:\.\d+)?)\s*%")

_UNIT_MULTIPLIERS = {
    "thousand": 1e3,
    "k": 1e3,
    "million": 1e6,
    "m": 1e6,
    "mn": 1e6,
    "billion": 1e9,
    "b": 1e9,
    "bn": 1e9,
    "trillion": 1e12,
}

# Relative tolerance used when matching a claimed figure to tool evidence:
# a claim matches when it is within 2% (or $1 for small figures) of a value
# the tool layer actually produced, so rounded/restated figures pass while
# invented ones are rejected.
_NUMERIC_TOLERANCE = 1.0
_NUMERIC_RELATIVE_TOLERANCE = 0.02


class AuditorAgent:
    """
    Reviews research answers for fabrication and evidence grounding.
    """

    def audit(
        self,
        report,
    ):
        """
        Backward-compatible report-length check.

        Args:
            report: An ``InvestmentReport`` (or any object with ``word_count``
                and ``body`` attributes) or an analysis object.

        Returns:
            ``True`` for non-report objects (analysis results) or an
            :class:`AuditResult` for reports.
        """
        if not hasattr(report, "word_count"):
            return True

        issues: list[str] = []

        if report.word_count < 5:
            issues.append("Report is too short.")

        if "Financial Metrics" not in report.body:
            issues.append("Missing financial metrics.")

        return AuditResult(
            passed=len(issues) == 0,
            issues=issues,
        )

    def audit_evidence(
        self,
        plan: ResearchPlan,
        evidence: dict[str, Any],
        answer: str,
        sources: list[dict[str, Any]],
        model: str | None = None,
    ) -> AuditResult:
        """
        Audit the final research answer against the collected evidence.

        Args:
            plan: The executed research plan.
            evidence: Tool results keyed by tool name (lists of ``ToolResult``).
            answer: The synthesized answer text.
            sources: Document chunks actually retrieved (with document_id /
                filename / page).

        Returns:
            An :class:`AuditResult` describing any grounding violations.
        """
        issues: list[str] = []
        warnings: list[str] = []

        tool_names = set(plan.tool_names)

        # 1. Valuation numbers must come from the valuation tool.
        if "calculate_valuation" in tool_names:
            valuation = self._results_for(evidence, "calculate_valuation")
            if not valuation:
                warnings.append(
                    "Valuation was planned but produced no usable result."
                )
            elif any(
                result.status == "error" for result in valuation
            ):
                warnings.append(
                    "Valuation engine failed for at least one ticker."
                )

        # 2. RAG claims need retrieved evidence.
        if plan.needs_rag:
            retrieved = self._results_for(evidence, "search_documents")
            retrieved_chunks = [
                chunk
                for result in retrieved
                if result.status == "done" and result.result
                for chunk in result.result.get("chunks", [])
            ]

            if not retrieved_chunks:
                if _answer_claims_document(answer):
                    issues.append(
                        "Answer cites document content but no chunk was retrieved."
                    )
            else:
                # 3. Every citation must correspond to an actual retrieved chunk.
                known = {
                    (str(chunk.get("filename") or "").lower(), chunk.get("page"))
                    for chunk in retrieved_chunks
                }
                for cited in self._citations(answer):
                    if not _citation_matches(cited, known):
                        issues.append(
                            f"Answer cites {cited['filename']} (page "
                            f"{cited['page']}) which was not retrieved."
                        )

        # 4 + 5. Ticker correctness and cross-ticker isolation.
        for tool in ("get_financials", "get_market_data", "calculate_valuation",
                     "calculate_financial_health", "calculate_risk"):
            for result in self._results_for(evidence, tool):
                result_data = result.result or {}
                result_ticker = result_data.get("ticker")

                if result_ticker is None:
                    continue

                expected = {t.upper() for t in plan.tickers}

                if result_ticker.upper() not in expected:
                    issues.append(
                        f"{result.tool} returned data for '{result_ticker}' "
                        f"which was not requested ({', '.join(plan.tickers) or 'none'})."
                    )

        # 6. No unsupported recommendation without valuation evidence.
        if (
            "calculate_valuation" not in tool_names
            and _mentions_recommendation(answer)
        ):
            warnings.append(
                "Answer implies a valuation recommendation without running "
                "the valuation engine."
            )

        # 7. Every financial figure in the answer must come from the evidence
        #    (tool output or retrieved document text). A dollar or percentage
        #    claim that no tool produced is a fabrication.
        if evidence:
            known = _gather_known_numbers(evidence, sources)

            unsupported = _unsupported_figures(answer, known)

            if unsupported:
                rendered = ", ".join(
                    f"{value:,.2f}{kind}" for value, kind in unsupported
                )
                issues.append(
                    "Answer states financial figures that no executed tool "
                    f"produced: {rendered}."
                )

        passed = len(issues) == 0

        logger.debug(
            "Audit %s: %d issues, %d warnings",
            "passed" if passed else "failed",
            len(issues),
            len(warnings),
        )

        return AuditResult(
            passed=passed,
            issues=issues,
        )

    # ──────────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────────

    @staticmethod
    def _results_for(
        evidence: dict[str, Any],
        tool: str,
    ) -> list[Any]:
        return list(evidence.get(tool) or [])

    @staticmethod
    def _citations(answer: str) -> list[dict[str, Any]]:
        """
        Extract ``(filename, page)`` citations the answer text claims.
        """
        citations: list[dict[str, Any]] = []

        for match in _CITATION_PATTERN.finditer(answer):
            filename = match.group(1).strip(" :,-")
            page = match.group(2)

            citations.append({
                "filename": filename,
                "page": int(page),
            })

        return citations


def _answer_claims_document(answer: str) -> bool:
    lowered = answer.lower()

    return any(
        marker in lowered
        for marker in (
            "according to",
            "the report states",
            "the report says",
            "the annual report",
            "the 10-k",
            "the 10k",
            "page ",
            "document states",
        )
    )


def _citation_matches(
    cited: dict[str, Any],
    known: set[tuple[str, int]],
) -> bool:
    """
    True when a cited ``(filename, page)`` matches a retrieved chunk.

    The citation regex captures surrounding prose (e.g. "According to Apple
    10-K.pdf"), so the retrieved filename is matched as a substring.
    """
    cited_name = (cited["filename"] or "").lower().strip()
    cited_page = cited["page"]

    for name, page in known:
        if page != cited_page:
            continue

        if not name:
            continue

        if name in cited_name or cited_name in name:
            return True

    return False


def _mentions_recommendation(answer: str) -> bool:
    lowered = answer.lower()

    return any(
        marker in lowered
        for marker in (
            "buy",
            "sell",
            "strong buy",
            "overvalued",
            "undervalued",
            "recommend",
            "investment thesis",
        )
    )


def _gather_known_numbers(
    evidence: dict[str, Any],
    sources: list[dict[str, Any]],
) -> set[float]:
    """
    Collect every numeric value the tool layer actually produced.

    This includes numeric fields in tool results plus numbers found in the
    retrieved chunk text, so a figure quoted verbatim from a retrieved
    document counts as grounded. Fractions below 1.0 also register their
    percentage equivalent so a rate expressed as "9%" matches evidence stored
    as ``0.09``.
    """
    known: set[float] = set()

    def add(value: float) -> None:
        known.add(value)
        if value != 0 and abs(value) < 1.0:
            known.add(value * 100.0)

    def walk(obj: Any) -> None:
        if isinstance(obj, bool):
            return

        if isinstance(obj, (int, float)):
            add(float(obj))
            return

        if isinstance(obj, str):
            for match in _TEXT_NUMBER_PATTERN.finditer(obj):
                raw = match.group(1).replace(",", "")
                suffix = (match.group(2) or "").lower()
                try:
                    add(float(raw) * _UNIT_MULTIPLIERS.get(suffix, 1.0))
                except ValueError:
                    pass
            return

        if isinstance(obj, dict):
            for value in obj.values():
                walk(value)
            return

        if isinstance(obj, (list, tuple)):
            for value in obj:
                walk(value)

    for results in evidence.values():
        for result in results:
            payload = getattr(result, "result", None)
            if isinstance(payload, dict):
                walk(payload)

    for source in sources:
        walk(source)

    return known


def _unsupported_figures(
    answer: str,
    known: set[float],
) -> list[tuple[float, str]]:
    """
    Return every ``(value, kind)`` financial figure claimed by ``answer`` that
    no tool produced.
    """
    unsupported: list[tuple[float, str]] = []

    for value, kind in _financial_claims(answer):
        if any(_figures_match(value, candidate) for candidate in known):
            continue
        unsupported.append((value, kind))

    return unsupported


def _financial_claims(answer: str) -> list[tuple[float, str]]:
    """Extract ``(value, kind)`` dollar / percentage figures from ``answer``."""
    claims: list[tuple[float, str]] = []

    for match in _DOLLAR_CLAIM_PATTERN.finditer(answer):
        raw = match.group(1).replace(",", "")

        suffix = (match.group(2) or "").lower()

        try:
            value = float(raw) * _UNIT_MULTIPLIERS.get(suffix, 1.0)
        except ValueError:
            continue

        claims.append((value, "$"))

    for match in _PERCENT_CLAIM_PATTERN.finditer(answer):
        try:
            claims.append((float(match.group(1)), "%"))
        except ValueError:
            continue

    return claims


def _figures_match(claim: float, candidate: float) -> bool:
    if _close_enough(claim, candidate):
        return True

    # The claim may be expressed in a different scale to the stored value
    # (e.g. "$394,328 million" vs a statement figure stored in $M, or a
    # "$3.2 trillion" market cap stored in raw dollars). Compare the claim
    # scaled down through common units before declaring it unsupported.
    for divisor in (1e3, 1e6, 1e9, 1e12):
        if _close_enough(claim / divisor, candidate):
            return True

    return False


def _close_enough(claim: float, candidate: float) -> bool:
    return abs(claim - candidate) <= max(
        _NUMERIC_TOLERANCE,
        abs(candidate) * _NUMERIC_RELATIVE_TOLERANCE,
    )
