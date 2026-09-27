from __future__ import annotations
import os
from unittest.mock import patch
import pytest
from sqlalchemy import text
POSTGRES_URL = os.getenv("TEST_POSTGRES_URL", "")
pytestmark = [
    pytest.mark.integration,
]
@pytest.fixture()
def postgres_manager():
    if not POSTGRES_URL:
        pytest.skip("TEST_POSTGRES_URL not set; PostgreSQL integration test skipped")
    try:
        import psycopg
    except ImportError:
        pytest.skip("psycopg driver not installed")
    from app.infrastructure.postgres import PostgreSQLManager
    with patch.dict(os.environ, {"DATABASE_URL": POSTGRES_URL}):
        manager = PostgreSQLManager()
        if not manager.health_check():
            manager.dispose()
            pytest.skip("PostgreSQL service not reachable at TEST_POSTGRES_URL")
        yield manager
        manager.dispose()
class TestPostgresIntegration:
    def test_connectivity_and_select(self, postgres_manager):
        assert postgres_manager.health_check() is True
        with postgres_manager.connect() as conn:
            value = conn.execute(text("SELECT 1")).scalar()
        assert value == 1
    def test_engine_uses_pre_ping_pool(self, postgres_manager):
        pool = postgres_manager.engine.pool
        assert pool._pre_ping is True
    def test_connection_survives_pool_recycle_cycle(self, postgres_manager):
        for _ in range(5):
            with postgres_manager.connect() as conn:
                assert conn.execute(text("SELECT 1")).scalar() == 1
    def test_chat_schema_creates_and_persists_on_postgres(self, postgres_manager):
        from app.chat.store import ChatStore
        store = ChatStore(POSTGRES_URL)
        store.save_turn(
            None,
            "pg-integration-session",
            user_message="hi",
            assistant_message="hello",
        )
        store2 = ChatStore(POSTGRES_URL)
        loaded = store2.get_session(None, "pg-integration-session")
        assert loaded is not None
        assert loaded["session_id"] == "pg-integration-session"
        assert store2.delete_session(None, "pg-integration-session") is True
