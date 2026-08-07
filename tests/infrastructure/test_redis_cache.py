from app.infrastructure.redis_cache import RedisCache


def test_redis():

    cache = RedisCache()

    assert isinstance(
        cache.ping(),
        bool,
    )