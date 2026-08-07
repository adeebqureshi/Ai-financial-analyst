"""
ChromaDB manager.
"""

from __future__ import annotations

import chromadb


class ChromaManager:

    def __init__(self) -> None:

        self.client = chromadb.Client()

    def heartbeat(self) -> bool:

        try:
            self.client.heartbeat()
            return True
        except Exception:
            return False