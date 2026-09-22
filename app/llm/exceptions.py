"""
LLM exceptions.
"""

from __future__ import annotations


class LLMError(Exception):
    """Base LLM exception."""


class ProviderError(LLMError):
    """Provider request failed."""


class AuthenticationError(ProviderError):
    """Authentication failed."""


class RateLimitError(ProviderError):
    """Rate limit exceeded."""


class TimeoutError(ProviderError):
    """Provider timed out."""