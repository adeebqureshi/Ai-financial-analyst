from app.infrastructure.logging import configure_logging


def test_logging():

    logger = configure_logging()

    logger.info("test")

    assert logger.name == "financial_analyst"