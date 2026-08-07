"""
Conversation memory.
"""

from __future__ import annotations

from app.llm.context import ContextWindow
from app.llm.conversation import Conversation
from app.llm.message import AssistantMessage
from app.llm.message import SystemMessage
from app.llm.message import UserMessage


class ConversationMemory:

    def __init__(self) -> None:
        self.conversation = Conversation()
        self.context = ContextWindow()

    def add_system(
        self,
        text: str,
    ) -> None:
        self.conversation.add(
            SystemMessage(text)
        )

    def add_user(
        self,
        text: str,
    ) -> None:
        self.conversation.add(
            UserMessage(text)
        )

    def add_assistant(
        self,
        text: str,
    ) -> None:
        self.conversation.add(
            AssistantMessage(text)
        )

    def trimmed_messages(self):
        return self.context.trim(
            self.conversation.messages
        )

    def clear(self) -> None:
        self.conversation.clear()