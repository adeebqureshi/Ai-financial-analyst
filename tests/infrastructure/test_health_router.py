from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.infrastructure.health_router import router


def test_health():

    app = FastAPI()

    app.include_router(router)

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200

    assert response.json()["healthy"]