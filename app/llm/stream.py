"""
Streaming utilities for LLM providers.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator


class TokenStream:
    """
    Simple synchronous token stream.
    """

    def __init__(
        self,
        tokens: Iterable[str],
    ) -> None:
        self._tokens = iter(tokens)

    def __iter__(self) -> Iterator[str]:
        return self

    def __next__(self) -> str:
        return next(self._tokens)

    def collect(self) -> str:
        return "".join(list(self))