import redis.asyncio as redis
from core.config import settings

# Shared connection pool to optimize local resource recycling
redis_pool = redis.ConnectionPool.from_url(
    settings.redis_url,
    decode_responses=True
)

async def get_redis() -> redis.Redis:
    """Dependency provider yielding an async Redis connection client."""
    return redis.Redis(connection_pool=redis_pool)