"""
Provider configuration.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderConfig:

    provider: str = "mock"

    model: str = "gpt-4.1"

    temperature: float = 0.2

    max_tokens: int = 4096

    timeout: int = 60