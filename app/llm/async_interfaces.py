from __future__ import annotations
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from app.llm.models import LLMRequest, LLMResponse
class AsyncLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
    @abstractmethod
    def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]: