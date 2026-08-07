"""
models.py

LLM request/response models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LLMRequest:

    prompt: str


@dataclass(slots=True)
class LLMResponse:

    text: str

    model: str