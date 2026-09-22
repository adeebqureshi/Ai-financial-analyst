from __future__ import annotations
class LLMError(Exception):
class ProviderError(LLMError):
class AuthenticationError(ProviderError):
class RateLimitError(ProviderError):
class TimeoutError(ProviderError):