from __future__ import annotations
import asyncio
import re
from collections.abc import AsyncIterator
from app.llm.async_interfaces import AsyncLLMProvider
from app.llm.models import LLMRequest, LLMResponse
from app.llm.usage import TokenUsage
class AsyncMockLLMProvider(AsyncLLMProvider):
    MODEL = "mock-llm"
    def __init__(
        self,
        delay: float = 0.0,
    ) -> None:
        self.delay = delay
    async def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        if self.delay:
            await asyncio.sleep(self.delay)
        return LLMResponse(
            text=f"LLM_RESPONSE:\n\n{request.prompt}",
            model=self.MODEL,
            usage=TokenUsage(
                prompt_tokens=len(request.prompt.split()),
                completion_tokens=5,
            ),
        )
    async def stream(
        self,
        request: LLMRequest,
    ) -> AsyncIterator[str]:
        response = await self.generate(request)
        for piece in re.split(r"(\s+)", response.text):
            if not piece:
                continue
            yield piece
            if self.delay:
                await asyncio.sleep(self.delay)