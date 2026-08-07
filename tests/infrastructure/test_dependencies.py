from app.infrastructure.dependencies import get_container


def test_dependencies():

    container = get_container()

    assert container is not None