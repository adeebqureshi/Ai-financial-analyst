from __future__ import annotations
import os
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
class _FakeDatabase:
    def __init__(self):
        self.disposed = False
        self.healthy = True
    def health_check(self):
        return self.healthy
    def dispose(self):
        self.disposed = True
class _FakeCache:
    def __init__(self):
        self.closed = False
        self.healthy = True
    def health_check(self):
        return self.healthy
    def close(self):
        self.closed = True
class _FakeVectorStore:
    def heartbeat(self):
        return True
def _fake_container():
    from app.infrastructure.container import Container
    container = Container.__new__(Container)
    container.database = _FakeDatabase()
    container.vector_store = _FakeVectorStore()
    return container
class TestContainerLifecycle:
    def test_health_reports_each_component_independently(self):
        container = _fake_container()
        checks = container.health()
        assert checks == {"database": True, "vector_store": True, "cache": True}
        container.database.healthy = False
        checks = container.health()
        assert checks["database"] is False
        assert checks["vector_store"] is True
    def test_close_disposes_database(self):
        container = _fake_container()
        container.close()
        assert container.database.disposed is True
    def test_shutdown_with_real_container_does_not_raise(self):
        from app.infrastructure.shutdown import shutdown
        from app.infrastructure.startup import startup
        container = startup()
        shutdown(container)
    def test_shutdown_is_idempotent(self):
        from app.infrastructure.shutdown import shutdown
        from app.infrastructure.startup import startup
        container = startup()
        shutdown(container)
        shutdown(container)
class TestHealthRouter:
    @pytest.fixture()
    def client(self):
        from app.infrastructure import health_router
        health_router.reset_health_container()
        app = FastAPI()
        app.include_router(health_router.router)
        yield TestClient(app)
        health_router.reset_health_container()
    def test_reports_healthy_when_critical_components_up(self, client, monkeypatch):
        class _Container:
            def health(self):
                return {"database": True, "cache": False, "vector_store": True}
        monkeypatch.setattr(
            "app.infrastructure.health_router._get_container", lambda: _Container()
        )
        body = client.get("/health").json()
        assert body["healthy"] is True
        assert body["database"] is True
        assert body["cache"] is False
        assert body["cache_optional"] is True
    def test_reports_degraded_when_database_down(self, client, monkeypatch):
        class _Container:
            def health(self):
                return {"database": False, "cache": True, "vector_store": True}
        monkeypatch.setattr(
            "app.infrastructure.health_router._get_container", lambda: _Container()
        )
        body = client.get("/health").json()
        assert body["healthy"] is False
        assert body["status"] == "degraded"
    def test_never_raises_on_container_failure(self, client, monkeypatch):
        def _boom():
            raise RuntimeError("container unavailable")
        monkeypatch.setattr("app.infrastructure.health_router._get_container", _boom)
        body = client.get("/health").json()
        assert body["healthy"] is False
        assert body["database"] is False
    def test_health_status_defaults_preserved(self):
        from app.infrastructure.health import HealthStatus
        status = HealthStatus()
        assert status.ok is True
        assert status.status == "healthy"
        assert HealthStatus(database=False).ok is False
