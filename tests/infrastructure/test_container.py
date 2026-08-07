from app.infrastructure.container import Container


def test_container():

    container = Container()

    assert container.database is not None

    assert container.cache is not None

    assert container.vector_store is not None