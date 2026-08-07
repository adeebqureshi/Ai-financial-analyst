"""
PostgreSQL connection manager.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine


class PostgreSQLManager:

    def __init__(self) -> None:

        self.url = os.getenv(
            "DATABASE_URL",
            "sqlite+pysqlite:///:memory:",
        )

        self.engine: Engine = create_engine(
            self.url,
            future=True,
        )

    def connect(self):

        return self.engine.connect()

    def dispose(self) -> None:

        self.engine.dispose()