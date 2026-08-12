"""
LLM provider registry.
"""

from __future__ import annotations

from collections.abc import Callable

from app.llm.providers.base import BaseLLMProvider


class ProviderRegistry:

    def __init__(self) -> None:
        self._providers: dict[str, Callable[[], BaseLLMProvider]] = {}

    def register(
        self,
        name: str,
        factory: Callable[[], BaseLLMProvider],
    ) -> None:
        self._providers[name.lower()] = factory

    def create(
        self,
        name: str,
        **kwargs: object,
    ) -> BaseLLMProvider:

        key = name.lower()

        if key not in self._providers:
            raise ValueError(f"Unknown provider: {name}")

        return self._providers[key](**kwargs)