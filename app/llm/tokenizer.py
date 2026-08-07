"""
Simple token estimation.
"""

from __future__ import annotations


class Tokenizer:

    @staticmethod
    def count(text: str) -> int:
        return len(text.split())

    @staticmethod
    def count_messages(messages) -> int:
        return sum(
            Tokenizer.count(message.content)
            for message in messages
        )