"""
Base loader interface.
"""

from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from app.ingestion.document import FinancialDocument


class DocumentLoader(ABC):

    @abstractmethod
    def load(
        self,
        path: str,
    ) -> FinancialDocument:
        """
        Load a financial document.
        """