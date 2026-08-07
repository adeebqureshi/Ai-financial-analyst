"""
Conversation message models.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Message:
    role: str
    content: str


class SystemMessage(Message):
    def __init__(self, content: str) -> None:
        super().__init__("system", content)


class UserMessage(Message):
    def __init__(self, content: str) -> None:
        super().__init__("user", content)


class AssistantMessage(Message):
    def __init__(self, content: str) -> None:
        super().__init__("assistant", content)