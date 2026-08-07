from app.infrastructure.health import HealthStatus


def test_health():

    health = HealthStatus()

    assert health.ok

    assert health.status == "healthy"