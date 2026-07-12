from fastapi import HTTPException, Request, status
import redis.asyncio as redis
from core.config import settings

async def verify_rate_limit(request: Request, redis_client: redis.Redis):
    """Enforces a strict sliding/fixed window rate limit per client IP via Redis."""

    client_ip = request.client.host if request.client else "unknown"
    cache_key = f"rate_limit:{client_ip}"
    
    # Atomic transaction execution using Redis pipeline
    async with redis_client.pipeline(transaction=True) as pipe:
        pipe.incr(cache_key)
        pipe.expire(cache_key, settings.rate_limit_window_sec)
        results = await pipe.execute()
        
    current_requests = results[0]
    
    if current_requests > settings.rate_limit_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please wait before submitting more logs."
        )