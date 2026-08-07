from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from app.infrastructure.middleware import RequestMiddleware


def test_middleware():

    app = FastAPI()

    middleware = RequestMiddleware()

    @app.middleware("http")
    async def _(request: Request, call_next):
        return await middleware(request, call_next)

    @app.get("/")
    async def root():
        return JSONResponse({"ok": True})

    client = TestClient(app)

    response = client.get("/")

    assert "X-Request-ID" in response.headers

    assert "X-Process-Time" in response.headers