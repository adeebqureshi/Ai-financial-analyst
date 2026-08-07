"""
Conversation context window.
"""

from __future__ import annotations

from app.llm.message import Message
from app.llm.tokenizer import Tokenizer


class ContextWindow:

    def __init__(
        self,
        max_tokens: int = 4096,
    ) -> None:

        self.max_tokens = max_tokens

    def trim(
        self,
        messages: list[Message],
    ) -> list[Message]:

        kept: list[Message] = []

        total = 0

        for message in reversed(messages):

            tokens = Tokenizer.count(message.content)

            if total + tokens > self.max_tokens:
                break

            kept.insert(0, message)

            total += tokens

        return kept