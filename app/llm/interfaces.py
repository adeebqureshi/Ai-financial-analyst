"""
interfaces.py

LLM interface definitions.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from app.llm.models import LLMRequest
from app.llm.models import LLMResponse


class LLMProvider(ABC):

    @abstractmethod
    def generate(
        self,
        request: LLMRequest,
    ) -> LLMResponse:
        """
        Generate an LLM response.
        """