"""
financial_analyst.py

Financial Analyst Agent.

Two responsibilities:

1. **Legacy quantitative analysis** (``analyze``) — wraps the existing
   ``FinancialAnalysisEngine``; used by ``FinancialPipeline`` for the
   ``/analyze`` and ``/report`` endpoints. Unchanged behaviour.

2. **Evidence-grounded synthesis** (``synthesize``) — produces the final
   research answer for the agentic chat pipeline. The model is only ever given
   structured tool output (real, retrieved data) and the actual retrieved
   sources. It is explicitly told to never fabricate numbers, page numbers or
   documents, and to say when evidence is insufficient.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.intents import AgentIntent
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.financial.analysis import FinancialAnalysisEngine
from app.financial.models import FinancialStatement
from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient

logger = get_logger(__name__)

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I couldn't find sufficient evidence to answer that question. "
    "No financial tool returned usable data and no uploaded document "
    "contained the information."
)


class FinancialAnalystAgent:

    def __init__(
        self,
        settings: Settings | None = None,
        llm_client: OpenAIClient | None = None,
    ) -> None:
        settings = settings or get_settings()

        self._settings = settings
        self._client = llm_client or OpenAIClient()
        self.engine = FinancialAnalysisEngine()

    # ──────────────────────────────────────────────────────────────────
    # Legacy quantitative analysis (used by FinancialPipeline)
    # ──────────────────────────────────────────────────────────────────

    def analyze(
        self,
        statement: FinancialStatement,
        current_price: float,
        growth_rate: float,
        risk_free_rate: float,
        beta: float,
        market_return: float,
        tax_rate: float,
        piotroski_score: int,
        altman_score: float,
        beneish_score: float,
    ):

        return self.engine.analyze(
            statement=statement,
            current_price=current_price,
            growth_rate=growth_rate,
            risk_free_rate=risk_free_rate,
            beta=beta,
            market_return=market_return,
            tax_rate=tax_rate,
            piotroski_score=piotroski_score,
            altman_score=altman_score,
            beneish_score=beneish_score,
        )

    # ──────────────────────────────────────────────────────────────────
    # Evidence-grounded synthesis (agentic chat pipeline)
    # ──────────────────────────────────────────────────────────────────

    def synthesize(
        self,
        query: str,
        intents: list[AgentIntent],
        evidence: dict[str, Any],
        sources: list[dict[str, Any]],
        tickers: list[str],
    ) -> tuple[str, str | None]:
        """
        Generate the final research answer from collected tool evidence.

        Args:
            query: The user question.
            intents: Detected intents (drives the answer structure).
            evidence: Tool results keyed by tool name (lists of ToolResult
                dicts). Only real, executed tool output is included.
            sources: Retrieved document chunks (with document_id / filename /
                page). Only actually retrieved chunks are passed.
            tickers: Tickers referenced by the answer.

        Returns:
            A ``(answer_text, model_name)`` tuple.
        """
        if not evidence:
            return INSUFFICIENT_EVIDENCE_MESSAGE, None

        evidence_block = json.dumps(
            _normalize_evidence(evidence),
            indent=2,
            default=str,
        )

        sources_block = _format_sources(sources)

        prompt = _build_synthesis_prompt(
            query=query,
            intents=intents,
            tickers=tickers,
            evidence=evidence_block,
            sources=sources_block,
            has_sources=bool(sources),
        )

        response = self._client.generate(LLMRequest(prompt=prompt))

        return response.text, getattr(response, "model", None)


def _normalize_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """
    Convert collected ``ToolResult`` objects into plain JSON-able structures.
    """
    normalized: dict[str, Any] = {}

    for tool, results in evidence.items():
        items: list[Any] = []

        for result in results:
            if isinstance(result, dict):
                items.append(result)
            else:
                items.append({
                    "tool": getattr(result, "tool", tool),
                    "status": getattr(result, "status", "error"),
                    "detail": getattr(result, "detail", ""),
                    "result": getattr(result, "result", None),
                    "error": getattr(result, "error", None),
                })

        if items:
            normalized[tool] = items

    return normalized


def _format_sources(sources: list[dict[str, Any]]) -> str:
    lines: list[str] = []

    for source in sources:
        filename = source.get("filename") or "Unknown document"
        page = source.get("page")

        if page is not None:
            lines.append(f"- {filename} (page {page})")
        else:
            lines.append(f"- {filename}")

    return "\n".join(lines)


def _build_synthesis_prompt(
    query: str,
    intents: list[AgentIntent],
    tickers: list[str],
    evidence: str,
    sources: str,
    has_sources: bool,
) -> str:
    intent_names = [intent.value for intent in intents]

    sections: list[str] = []

    sections.append("**Executive Conclusion** — 2-4 sentence verdict")

    if AgentIntent.FINANCIAL_ANALYSIS.value in intent_names or (
        "get_financials" in evidence or "calculate_ratios" in evidence
    ):
        sections.append(
            "**Financial Analysis** — revenue, margins, profitability and "
            "key ratios, using only the numbers in the evidence."
        )

    if AgentIntent.VALUATION.value in intent_names or "calculate_valuation" in evidence:
        sections.append(
            "**Valuation** — current price, intrinsic value, upside and "
            "what the valuation implies (undervalued/overvalued)."
        )

    if "calculate_financial_health" in evidence:
        sections.append(
            "**Financial Health** — health score, rating, Piotroski / Altman "
            "/ Beneish interpretation."
        )

    if "calculate_risk" in evidence or AgentIntent.RISK_ANALYSIS.value in intent_names:
        sections.append(
            "**Risk** — risk level and the key risk signals from the evidence."
        )

    if has_sources:
        sections.append(
            "**Document Evidence** — summarise what the retrieved document "
            "chunks say, citing each with its filename and page number."
        )

    if any(
        intent.value in intent_names
        for intent in (
            AgentIntent.VALUATION,
            AgentIntent.COMPARISON,
            AgentIntent.FINANCIAL_ANALYSIS,
        )
    ):
        sections.append(
            "**Investment Thesis** — a balanced, evidence-based conclusion. "
            "Do not fabricate a recommendation; if the evidence is "
            "insufficient, say so."
        )

    sections.append("**Sources** — list the document sources actually cited.")

    section_list = "\n".join(
        f"{index}. {section}" for index, section in enumerate(sections, start=1)
    )

    ticker_line = ", ".join(tickers) if tickers else "None detected"

    return f"""You are the final research analyst in an evidence-grounded financial agent.

A real tool layer already produced the structured evidence below. The evidence
comes exclusively from executed tools; the sources come exclusively from
retrieval. You must answer the question using ONLY this evidence.

RULES:
- Every number you state MUST come from the evidence JSON. Do not invent or
  approximate any figure, score, price or percentage.
- Do NOT make up document names, page numbers or quotes. Only cite sources
  that are listed below. If you need a fact that is not in the evidence, say
  the information is unavailable.
- Do not reveal internal chain-of-thought, tool planning or reasoning. Only
  present the final analysis.
- Structure the answer with ONLY the relevant sections from this list:

{section_list}

If the evidence is empty or irrelevant to the question, answer with exactly:
"{INSUFFICIENT_EVIDENCE_MESSAGE}"

Question: {query}

Tickers referenced: {ticker_line}

--- SOURCES (only cite these) ---
{sources}

--- EVIDENCE (structured tool output) ---
{evidence}
"""


__all__ = [
    "FinancialAnalystAgent",
    "INSUFFICIENT_EVIDENCE_MESSAGE",
]
