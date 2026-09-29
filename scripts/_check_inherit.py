"""Verify the subclasses now inherit BaseLLMProvider.stream."""

from __future__ import annotations

from app.llm.models import LLMRequest
from app.llm.providers.base import BaseLLMProvider
from app.llm.providers.mock import MockLLMProvider
from app.llm.providers.openai_provider import OpenAIProvider

for cls in (MockLLMProvider, OpenAIProvider):
    assert "stream" not in cls.__dict__, f"{cls.__name__} still overrides stream"
    assert cls.stream is BaseLLMProvider.stream, f"{cls.__name__} not inheriting"
    print(f"{cls.__name__}: inherits BaseLLMProvider.stream  OK")

# The inherited implementation must still behave the same.
provider = MockLLMProvider()
tokens = list(provider.stream(LLMRequest(prompt="hello world foo")))
assert tokens == ["hello ", "world ", "foo "], tokens
print("inherited stream output:", tokens)

print("\nINHERITANCE VERIFIED")
