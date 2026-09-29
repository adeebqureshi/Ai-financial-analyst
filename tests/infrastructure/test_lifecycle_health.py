from __future__ import annotations
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
class TestHealthStatus:
    def test_health_status_defaults_preserved(self):
        from app.infrastructure.health import HealthStatus
        status = HealthStatus()
        assert status.ok is True
        assert status.status == "healthy"
        assert HealthStatus(database=False).ok is False
