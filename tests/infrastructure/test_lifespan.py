import pytest
from fastapi import FastAPI

from app.infrastructure.lifespan import lifespan


@pytest.mark.anyio
async def test_lifespan():

    app = FastAPI()

    async with lifespan(app):
        assert app.state.container is not None