"""
report_generator.py

LLM report generator.
"""

from __future__ import annotations

from app.llm.models import LLMRequest
from app.llm.openai_client import OpenAIClient
from app.llm.prompt_builder import PromptBuilder
from app.reports.markdown_report import MarkdownReport


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

        prompt = PromptBuilder.build(
            query=query,
            context=context,
            report=report,
        )

        response = self.client.generate(
            LLMRequest(prompt=prompt),
        )

        return response.text