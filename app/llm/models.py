"""
LLM request and response models.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.llm.usage import TokenUsage


@dataclass(slots=True)
class LLMRequest:
    prompt: str


@dataclass(slots=True)
class LLMResponse:
    text: str
    model: str
    usage: TokenUsage | None = None