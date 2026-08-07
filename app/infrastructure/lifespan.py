"""
FastAPI lifespan.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.infrastructure.startup import startup
from app.infrastructure.shutdown import shutdown


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncIterator[None]:

    container = startup()

    app.state.container = container

    yield

    shutdown(container)