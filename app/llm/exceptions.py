
from __future__ import annotations


class LLMError(Exception):
        pass


class ProviderError(LLMError):
        pass


class AuthenticationError(ProviderError):
        pass


class RateLimitError(ProviderError):
        pass


class TimeoutError(ProviderError):
        pass
