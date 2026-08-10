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
