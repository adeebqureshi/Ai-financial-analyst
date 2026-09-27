from app.infrastructure.container import Container


def test_container():
    container = Container()
    assert container.database is not None
    assert container.vector_store is not None


def test_health_reports_database_and_qdrant():
    container = Container()
    checks = container.health()
    assert set(checks) == {"database", "vector_store", "cache"}
    assert isinstance(checks["vector_store"], bool)
    container.close()
