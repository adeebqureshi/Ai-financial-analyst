"""
Infrastructure lifecycle, health, rate-limiter resilience and Docker wiring
tests. No external services required.
"""

from __future__ import annotations

import os

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


# ──────────────────────────────────────────────────────────────────────────────
# Container lifecycle
# ──────────────────────────────────────────────────────────────────────────────

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
    container.cache = _FakeCache()
    container.vector_store = _FakeVectorStore()
    return container


class TestContainerLifecycle:
    def test_health_reports_each_component_independently(self):
        container = _fake_container()

        checks = container.health()
        assert checks == {"database": True, "cache": True, "vector_store": True}

        container.database.healthy = False
        container.cache.healthy = False
        checks = container.health()
        assert checks["database"] is False
        assert checks["cache"] is False
        assert checks["vector_store"] is True  # independent probes

    def test_close_disposes_database_and_closes_cache(self):
        container = _fake_container()

        container.close()

        assert container.database.disposed is True
        assert container.cache.closed is True

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
        shutdown(container)  # second call must not raise


# ──────────────────────────────────────────────────────────────────────────────
# Health router
# ──────────────────────────────────────────────────────────────────────────────

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
        # Cache is optional and never degrades overall health.
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


# ──────────────────────────────────────────────────────────────────────────────
# Rate limiter: Redis failure / recovery behaviour
# ──────────────────────────────────────────────────────────────────────────────

class TestRateLimiterRedisRecovery:
    def _backend_with_client(self, client):
        from app.api.rate_limiter import RedisBackend

        backend = RedisBackend.__new__(RedisBackend)
        backend._redis_url = "redis://localhost:6379/0"
        backend._client = client
        backend._last_connect_attempt = 0.0
        return backend

    def test_increment_failure_drops_client_for_reconnect(self):
        class _Fail:
            def pipeline(self):
                raise ConnectionError("redis down")

        backend = self._backend_with_client(_Fail())

        with pytest.raises(ConnectionError):
            backend.increment("k", 60)

        assert backend._client is None

    def test_no_reconnect_before_cooldown(self):
        import time as time_mod

        calls = []
        backend = self._backend_with_client(None)
        backend._last_connect_attempt = time_mod.monotonic()

        def _fake_connect():
            calls.append(1)
            backend._client = object()

        backend._connect = _fake_connect
        assert backend._ensure_client() is None
        assert calls == []

    def test_reconnects_after_cooldown(self):
        import time as time_mod

        calls = []
        backend = self._backend_with_client(None)
        backend._last_connect_attempt = time_mod.monotonic() - 60.0

        def _fake_connect():
            calls.append(1)
            backend._client = "connected"

        backend._connect = _fake_connect
        assert backend._ensure_client() == "connected"
        assert calls == [1]

    def test_hybrid_limiter_recovers_to_redis_after_outage(self):
        import time as time_mod

        from app.api import rate_limiter as rl

        class _ProbeBackend:
            def __init__(self):
                self.healthy = False

            def health_check(self):
                return self.healthy

        limiter = rl.HybridRateLimiter.__new__(rl.HybridRateLimiter)
        limiter._settings = rl.get_settings()
        limiter._redis_backend = _ProbeBackend()
        limiter._local_backend = rl.LocalMemoryBackend()
        limiter._use_redis = False
        limiter._backend = limiter._local_backend
        limiter._last_redis_probe = time_mod.monotonic() - 999.0

        backend = limiter._get_backend()
        assert backend is limiter._local_backend

        # Redis comes back.
        limiter._redis_backend.healthy = True
        limiter._last_redis_probe = time_mod.monotonic() - 999.0
        backend = limiter._get_backend()
        assert backend is limiter._redis_backend
        assert limiter._use_redis is True

    def test_hybrid_limiter_falls_back_when_redis_dies(self):
        from app.api import rate_limiter as rl

        class _ProbeBackend:
            def __init__(self):
                self.healthy = True

            def health_check(self):
                return self.healthy

        limiter = rl.HybridRateLimiter.__new__(rl.HybridRateLimiter)
        limiter._settings = rl.get_settings()
        limiter._redis_backend = _ProbeBackend()
        limiter._local_backend = rl.LocalMemoryBackend()
        limiter._use_redis = True
        limiter._backend = limiter._redis_backend
        limiter._last_redis_probe = 0.0

        limiter._redis_backend.healthy = False
        backend = limiter._get_backend()
        assert backend is limiter._local_backend
        assert limiter._use_redis is False

    def test_local_backend_still_healthy(self):
        from app.api.rate_limiter import LocalMemoryBackend

        backend = LocalMemoryBackend()
        assert backend.health_check() is True
        assert backend.increment("k", 60) == 1


# ──────────────────────────────────────────────────────────────────────────────
# Chat/auth engine lifecycle
# ──────────────────────────────────────────────────────────────────────────────

class TestAppEngineLifecycle:
    def test_chat_engines_are_cached_and_disposable(self, tmp_path):
        from app.chat import database as chat_db

        url1 = f"sqlite:///{tmp_path / 'a.db'}"
        url2 = f"sqlite:///{tmp_path / 'b.db'}"

        e1 = chat_db.get_engine(url1)
        assert chat_db.get_engine(url1) is e1

        chat_db.dispose_all_engines()

        # After disposal a new engine is built and the old one is closed.
        e1b = chat_db.get_engine(url1)
        assert e1b is not e1
        assert url2 not in chat_db._engines
        chat_db.dispose_all_engines()

    def test_chat_sqlite_file_gets_wal_pragmas(self, tmp_path):
        from app.chat import database as chat_db

        url = f"sqlite:///{tmp_path / 'wal.db'}"
        engine = chat_db.get_engine(url)

        with engine.connect() as conn:
            mode = conn.exec_driver_sql("PRAGMA journal_mode").scalar()

        assert str(mode).lower() == "wal"
        chat_db.dispose_all_engines()

    def test_auth_engines_are_cached_and_disposable(self, tmp_path):
        from app.auth import database as auth_db

        url = f"sqlite:///{tmp_path / 'auth.db'}"
        e1 = auth_db._engine_for(url)
        assert auth_db._engine_for(url) is e1

        auth_db.dispose_all_engines()

        e1b = auth_db._engine_for(url)
        assert e1b is not e1
        auth_db.dispose_all_engines()

    def test_chat_store_works_end_to_end_on_sqlite(self, tmp_path):
        from app.chat.store import ChatStore

        store = ChatStore(f"sqlite:///{tmp_path / 'chat.db'}")
        store.save_turn(
            None,
            "lifecycle-session",
            user_message="hi",
            assistant_message="hello",
        )
        loaded = store.get_session(None, "lifecycle-session")
        assert loaded is not None
        assert loaded["session_id"] == "lifecycle-session"


# ──────────────────────────────────────────────────────────────────────────────
# Docker wiring
# ──────────────────────────────────────────────────────────────────────────────

class TestDockerWiring:
    @pytest.fixture()
    def compose(self):
        yaml = pytest.importorskip("yaml")
        path = os.path.join(
            os.path.dirname(__file__), "..", "..", "docker", "docker-compose.yml"
        )
        with open(path, encoding="utf-8") as fh:
            return yaml.safe_load(fh)

    def test_app_uses_postgres_for_all_stores(self, compose):
        env = compose["services"]["app"]["environment"]
        assert env["DATABASE_URL"].startswith("postgresql+psycopg://")
        assert env["AUTH_DATABASE_URL"].startswith("postgresql+psycopg://")
        assert env["CHAT_DATABASE_URL"].startswith("postgresql+psycopg://")

    def test_app_wired_to_redis(self, compose):
        env = compose["services"]["app"]["environment"]
        assert env["RATE_LIMIT_REDIS_URL"].startswith("redis://redis:")
        assert env["CHAT_REDIS_URL"].startswith("redis://redis:")

    def test_app_waits_for_healthy_dependencies(self, compose):
        depends = compose["services"]["app"]["depends_on"]
        assert depends["postgres"]["condition"] == "service_healthy"
        assert depends["redis"]["condition"] == "service_healthy"

    def test_datastores_have_healthchecks_and_persistence(self, compose):
        pg = compose["services"]["postgres"]
        rd = compose["services"]["redis"]

        assert "healthcheck" in pg
        assert "healthcheck" in rd
        assert any("postgres-data" in str(v) for v in pg["volumes"])
        assert any("redis-data" in str(v) for v in rd["volumes"])

    def test_app_has_healthcheck(self, compose):
        assert "healthcheck" in compose["services"]["app"]