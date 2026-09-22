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
_TEXT_NUMBER_PATTERN = re.compile(
    r"(-?\d[\d,]*(?:\.\d+)?)\s*"
    r"(thousand|million|billion|trillion|mn|bn|k|m|b)?",
    re.IGNORECASE,
)
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
_NUMERIC_TOLERANCE = 1.0
_NUMERIC_RELATIVE_TOLERANCE = 0.02
class AuditorAgent:
    def audit(
        self,
        report,
    ):
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
        issues: list[str] = []
        warnings: list[str] = []
        notes: list[str] = []
        tool_names = set(plan.tool_names)
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
        if (
            "calculate_valuation" not in tool_names
            and _mentions_recommendation(answer)
        ):
            warnings.append(
                "Answer implies a valuation recommendation without running "
                "the valuation engine."
            )
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
        if "run_calculation" in tool_names:
            for result in self._results_for(evidence, "run_calculation"):
                payload = result.result or {}
                if result.status != "done" or payload.get("status") != "computed":
                    issues.append(
                        "A sandboxed calculation failed; its value must not be "
                        "cited in the answer."
                    )
                    continue
                if payload.get("computed_by") == "sandbox":
                    notes.append(
                        "Calculation result was computed by the sandbox from "
                        "application-supplied context, not asserted by the LLM."
                    )
        passed = len(issues) == 0
        logger.debug(
            "Audit %s: %d issues, %d warnings, %d notes",
            "passed" if passed else "failed",
            len(issues),
            len(warnings),
            len(notes),
        )
        return AuditResult(
            passed=passed,
            issues=issues,
            notes=notes,
        )
    @staticmethod
    def _results_for(
        evidence: dict[str, Any],
        tool: str,
    ) -> list[Any]:
        return list(evidence.get(tool) or [])
    @staticmethod
    def _citations(answer: str) -> list[dict[str, Any]]:
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
                numeric_payload = {
                    key: value
                    for key, value in payload.items()
                    if key not in ("code", "question", "output")
                }
                walk(numeric_payload)
    for source in sources:
        walk(source)
    return known
def _unsupported_figures(
    answer: str,
    known: set[float],
) -> list[tuple[float, str]]:
    unsupported: list[tuple[float, str]] = []
    for value, kind in _financial_claims(answer):
        if any(_figures_match(value, kind, candidate) for candidate in known):
            continue
        unsupported.append((value, kind))
    return unsupported
def _financial_claims(answer: str) -> list[tuple[float, str]]:
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
def _figures_match(claim: float, kind: str, candidate: float) -> bool:
    if kind == "%":
        return abs(claim - candidate) <= (
            abs(candidate) * _NUMERIC_RELATIVE_TOLERANCE + 1e-6
        )
    if _close_enough(claim, candidate):
        return True
    for divisor in (1e3, 1e6, 1e9, 1e12):
        if _close_enough(claim / divisor, candidate):
            return True
    return False
def _close_enough(claim: float, candidate: float) -> bool:
    return abs(claim - candidate) <= max(
        _NUMERIC_TOLERANCE,
        abs(candidate) * _NUMERIC_RELATIVE_TOLERANCE,
    )