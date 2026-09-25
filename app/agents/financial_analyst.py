"""
financial_analyst.py

Financial Analyst Agent.

Two responsibilities:

1. Legacy quantitative analysis (``analyze``) — wraps the existing
   ``FinancialAnalysisEngine``; used by ``FinancialPipeline`` for the
   ``/analyze`` and ``/report`` endpoints.

2. Evidence-grounded synthesis (``synthesize``) — produces the final
   research answer for the agentic chat pipeline.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

from app.agents.intents import AgentIntent
from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.financial.analysis import FinancialAnalysisEngine
from app.financial.models import FinancialStatement
from app.llm.async_openai_client import AsyncOpenAIClient
from app.llm.exceptions import LLMError
from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient

logger = get_logger(__name__)

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "I couldn't find sufficient evidence to answer that question. "
    "No financial tool returned usable data and no uploaded document "
    "contained the information."
)

LLM_UNAVAILABLE_MESSAGE = (
    "I could not complete the synthesis because the language model is "
    "currently unavailable (missing or invalid API key, provider error, "
    "timeout, or rate limit). The structured tool results were computed but "
    "could not be summarized."
)

# Hard safety boundary for retrieved RAG context.
MAX_RAG_CONTEXT_TOKENS = 100_000


class FinancialAnalystAgent:

    def __init__(
        self,
        settings: Settings | None = None,
        llm_client: OpenAIClient | None = None,
        async_client: AsyncOpenAIClient | None = None,
    ) -> None:
        settings = settings or get_settings()

        self._settings = settings
        self._client = llm_client or OpenAIClient()
        self._async_client = async_client
        self.engine = FinancialAnalysisEngine()

    def ensure_async_client(self) -> AsyncOpenAIClient:
        """
        Return the async LLM client, building it once on first use.

        The client is built lazily so that synchronous callers (``synthesize``)
        never construct the async provider unnecessarily.
        """
        if self._async_client is None:
            self._async_client = AsyncOpenAIClient()

        return self._async_client

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

        Retrieved RAG context is hard-limited to 100,000 tokens before it is
        placed into the synthesis prompt.
        """
        if not evidence:
            return INSUFFICIENT_EVIDENCE_MESSAGE, None

        evidence_block = json.dumps(
            _normalize_evidence(evidence),
            indent=2,
            default=str,
        )

        sources_block = _format_sources(
            _truncate_sources(sources)
        )

        prompt = _build_synthesis_prompt(
            query=query,
            intents=intents,
            tickers=tickers,
            evidence=evidence_block,
            sources=sources_block,
            has_sources=bool(sources),
        )

        try:
            response = self._client.generate(
                LLMRequest(prompt=prompt),
            )
        except LLMError as exc:
            import traceback

            logger.error(
                "LLM synthesis FULL ERROR for query %s: %s\n%s",
                query[:120],
                exc,
                traceback.format_exc(),
            )
            return LLM_UNAVAILABLE_MESSAGE, None

        except Exception as exc:
            import traceback

            logger.error(
                "LLM synthesis UNEXPECTED ERROR: %s\n%s",
                exc,
                traceback.format_exc(),
            )
            return LLM_UNAVAILABLE_MESSAGE, None

        return response.text, getattr(response, "model", None)

    # ──────────────────────────────────────────────────────────────────
    # Streaming evidence-grounded synthesis
    # ──────────────────────────────────────────────────────────────────

    async def stream_synthesize(
        self,
        query: str,
        intents: list[AgentIntent],
        evidence: dict[str, Any],
        sources: list[dict[str, Any]],
        tickers: list[str],
    ) -> AsyncIterator[str]:
        """
        Stream the final research answer token-by-token.

        Retrieved RAG context is hard-limited to 100,000 tokens before it is
        placed into the synthesis prompt.
        """
        if not evidence:
            yield INSUFFICIENT_EVIDENCE_MESSAGE
            return

        evidence_block = json.dumps(
            _normalize_evidence(evidence),
            indent=2,
            default=str,
        )

        sources_block = _format_sources(
            _truncate_sources(sources)
        )

        prompt = _build_synthesis_prompt(
            query=query,
            intents=intents,
            tickers=tickers,
            evidence=evidence_block,
            sources=sources_block,
            has_sources=bool(sources),
        )

        try:
            async for token in self.ensure_async_client().stream(
                LLMRequest(prompt=prompt)
            ):
                yield token

        except LLMError as exc:
            import traceback

            logger.error(
                "Streaming LLM synthesis LLMError for query %s: %s\n%s",
                query[:120],
                exc,
                traceback.format_exc(),
            )
            yield LLM_UNAVAILABLE_MESSAGE

        except Exception as exc:
            import traceback

            logger.error(
                "Streaming LLM synthesis UNEXPECTED ERROR for query %s: %s\n%s",
                query[:120],
                exc,
                traceback.format_exc(),
            )
            yield LLM_UNAVAILABLE_MESSAGE


def _normalize_evidence(
    evidence: dict[str, Any],
) -> dict[str, Any]:
    """
    Convert collected ToolResult objects into plain JSON-able structures.
    """
    normalized: dict[str, Any] = {}

    for tool, results in evidence.items():
        items: list[Any] = []

        for result in results:
            if isinstance(result, dict):
                items.append(result)
            else:
                items.append(
                    {
                        "tool": getattr(result, "tool", tool),
                        "status": getattr(result, "status", "error"),
                        "detail": getattr(result, "detail", ""),
                        "result": getattr(result, "result", None),
                        "error": getattr(result, "error", None),
                    }
                )

        if items:
            normalized[tool] = items

    return normalized


def _source_text(source: dict[str, Any]) -> str:
    """
    Extract the actual retrieved text from a source.

    Supports the common field names used by retrieval pipelines.
    """
    for key in (
        "text",
        "content",
        "chunk",
        "page_content",
        "document",
    ):
        value = source.get(key)

        if value is not None:
            return str(value)

    return ""


def _estimate_tokens(text: str) -> int:
    """
    Estimate tokens using the project's tokenizer when available.

    Falls back to whitespace counting so the hard boundary still works even
    if the tokenizer module cannot be imported.
    """
    if not text:
        return 0

    try:
        from app.llm.tokenizer import Tokenizer

        return Tokenizer.count(text)
    except Exception:
        return len(text.split())


def _truncate_text_to_tokens(
    text: str,
    max_tokens: int,
) -> str:
    """
    Hard-limit text to the requested token budget.

    The project's Tokenizer currently counts whitespace-separated tokens, so
    truncation is performed using the same representation.
    """
    if max_tokens <= 0:
        return ""

    if _estimate_tokens(text) <= max_tokens:
        return text

    words = text.split()

    return " ".join(words[:max_tokens])


def _truncate_sources(
    sources: list[dict[str, Any]],
    max_tokens: int = MAX_RAG_CONTEXT_TOKENS,
) -> list[dict[str, Any]]:
    """
    Apply a hard 100,000-token limit to retrieved RAG context.

    Sources are preserved in retrieval order. Complete sources are retained
    whenever possible. If the final source exceeds the remaining budget, only
    its text is truncated.

    Metadata such as filename and page is retained so citations remain
    meaningful.
    """
    if max_tokens <= 0 or not sources:
        return []

    truncated: list[dict[str, Any]] = []
    remaining = max_tokens

    for source in sources:
        if remaining <= 0:
            break

        copied = dict(source)
        text = _source_text(copied)

        if not text:
            # Metadata-only source consumes no RAG token budget.
            truncated.append(copied)
            continue

        text_tokens = _estimate_tokens(text)

        if text_tokens <= remaining:
            truncated.append(copied)
            remaining -= text_tokens
            continue

        copied_text = _truncate_text_to_tokens(
            text,
            remaining,
        )

        if copied_text:
            copied["text"] = copied_text

            # Remove alternate content fields so the same text cannot
            # accidentally be included twice downstream.
            for key in (
                "content",
                "chunk",
                "page_content",
                "document",
            ):
                if key != "text":
                    copied.pop(key, None)

            truncated.append(copied)

        remaining = 0

    original_tokens = sum(
        _estimate_tokens(_source_text(source))
        for source in sources
    )

    used_tokens = max_tokens - remaining

    if original_tokens > max_tokens:
        logger.warning(
            "RAG context truncated: original_tokens=%d "
            "limit=%d retained_tokens=%d sources=%d retained_sources=%d",
            original_tokens,
            max_tokens,
            used_tokens,
            len(sources),
            len(truncated),
        )

    return truncated


def _format_sources(
    sources: list[dict[str, Any]],
) -> str:
    lines: list[str] = []

    for source in sources:
        filename = source.get("filename") or "Unknown document"
        page = source.get("page")
        text = _source_text(source)

        if page is not None:
            header = f"- {filename} (page {page})"
        else:
            header = f"- {filename}"

        if text:
            lines.append(f"{header}\n{text}")
        else:
            lines.append(header)

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

    sections.append(
        "**Executive Conclusion** — 2-4 sentence verdict"
    )

    if (
        AgentIntent.FINANCIAL_ANALYSIS.value in intent_names
        or "get_financials" in evidence
        or "calculate_ratios" in evidence
    ):
        sections.append(
            "**Financial Analysis** — revenue, margins, profitability and "
            "key ratios, using only the numbers in the evidence."
        )

    if (
        AgentIntent.VALUATION.value in intent_names
        or "calculate_valuation" in evidence
    ):
        sections.append(
            "**Valuation** — current price, intrinsic value, upside and "
            "what the valuation implies (undervalued/overvalued)."
        )

    if "calculate_financial_health" in evidence:
        sections.append(
            "**Financial Health** — health score, rating, Piotroski / Altman "
            "/ Beneish interpretation."
        )

    if (
        "calculate_risk" in evidence
        or AgentIntent.RISK_ANALYSIS.value in intent_names
    ):
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

    if has_sources:
        sections.append(
            "**Sources** — list the document sources actually cited."
        )

    section_list = "\n".join(
        f"{index}. {section}"
        for index, section in enumerate(
            sections,
            start=1,
        )
    )

    ticker_line = (
        ", ".join(tickers)
        if tickers
        else "None detected"
    )

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
    "MAX_RAG_CONTEXT_TOKENS",
]