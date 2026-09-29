
from __future__ import annotations


class LLMError(Exception):
        pass


class ProviderError(LLMError):
        pass


class AuthenticationError(ProviderError):
        pass


class RateLimitError(ProviderError):
    """Raised when the LLM provider rejects a request due to rate limiting.

    ``retry_after`` carries the server-advised wait in seconds when the
    provider communicates one (e.g. "Please retry in 17.6s"). The retry
    policy uses it so it does not burn through every attempt faster than
    the quota window actually resets.
    """

    def __init__(self, *args: object, retry_after: float | None = None) -> None:
        super().__init__(*args)
        self.retry_after = retry_after


class TimeoutError(ProviderError):
        pass
