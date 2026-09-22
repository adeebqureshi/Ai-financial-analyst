from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.core.config import Settings
@dataclass(frozen=True)
class ProviderConfig:
    provider: str = "mock"
    model: str = "gpt-4.1"
    temperature: float = 0.2
    max_tokens: int = 4096
    timeout: int = 60
    @classmethod
    def from_settings(
        cls,
        settings: Settings,
    ) -> ProviderConfig:
        return cls(
            provider=settings.llm_provider,
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            timeout=settings.api_timeout,
        )