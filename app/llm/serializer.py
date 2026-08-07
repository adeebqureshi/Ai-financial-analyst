"""
Conversation serialization.
"""

from __future__ import annotations

from app.llm.message import Message


class MessageSerializer:

    @staticmethod
    def to_dict(
        message: Message,
    ) -> dict:

        return {
            "role": message.role,
            "content": message.content,
        }

    @staticmethod
    def to_list(
        messages: list[Message],
    ) -> list[dict]:

        return [
            MessageSerializer.to_dict(m)
            for m in messages
        ]