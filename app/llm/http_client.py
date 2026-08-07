"""
Reusable HTTP client for LLM providers.
"""

from __future__ import annotations

import httpx


class LLMHttpClient:

    def __init__(
        self,
        timeout: float = 60.0,
    ) -> None:

        self._client = httpx.Client(
            timeout=timeout,
        )

    @property
    def client(self) -> httpx.Client:
        return self._client

    def close(self) -> None:
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.close()