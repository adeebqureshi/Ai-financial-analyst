"""
prompt_builder.py

LLM prompt builder.
"""

from __future__ import annotations


class PromptBuilder:

    @staticmethod
    def build(
        query: str,
        context: str,
        report: str,
    ) -> str:

        return f"""You are a professional financial analyst.

User Question:
{query}

Retrieved Context:
{context}

Financial Analysis:
{report}

Instructions:

- Answer only using the provided context.
- If information is missing, state it.
- Do not hallucinate.
- Explain reasoning clearly.
- End with an investment conclusion.
"""