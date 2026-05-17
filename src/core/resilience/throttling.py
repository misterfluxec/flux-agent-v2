from fastapi import HTTPException
from redis.asyncio import Redis
import time

class TenantThrottler:
    """
    Throttling consciente del tenant (Sliding Window simple).
    Devuelve 429 Too Many Requests si se excede para proteger las colas.
    """
    def __init__(self, redis: Redis, default_limit: int = 100, default_window: int = 60):
        self.redis = redis
        self.limit = default_limit
        self.window = default_window

    async def check_rate_limit(self, tenant_id: str, endpoint: str = "global"):
        redis_key = f"throttle:{tenant_id}:{endpoint}"
        
        current = await self.redis.incr(redis_key)
        if current == 1:
            await self.redis.expire(redis_key, self.window)
            
        if current > self.limit:
            raise HTTPException(
                status_code=429, 
                detail="Too Many Requests. Tenant rate limit exceeded."
            )
