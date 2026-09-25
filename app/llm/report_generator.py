from __future__ import annotations

from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.llm.prompt_builder import PromptBuilder
from app.reports.markdown_report import MarkdownReport


MAX_RAG_CONTEXT_TOKENS = 100_000


def _truncate_context(context: str, max_tokens: int = MAX_RAG_CONTEXT_TOKENS) -> str:
    """Hard-limit retrieved context before it reaches the report LLM."""
    if not context:
        return ""
    if max_tokens <= 0:
        return ""
    words = context.split()
    if len(words) <= max_tokens:
        return context
    return " ".join(words[:max_tokens])


class ReportGenerator:
    def __init__(self) -> None:
        self.client = OpenAIClient()

    def generate(
        self,
        query: str,
        context: str,
        result: dict,
    ) -> str:
        report = MarkdownReport.generate(result)
        safe_context = _truncate_context(context)
        prompt = PromptBuilder.build(
            query=query,
            context=safe_context,
            report=report,
        )
        response = self.client.generate(
            LLMRequest(prompt=prompt),
        )
        return response.text


__all__ = [
    "ReportGenerator",
    "MAX_RAG_CONTEXT_TOKENS",
]
