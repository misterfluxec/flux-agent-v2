from fastapi import Depends
from redis.asyncio import Redis, from_url

from src.config import obtener_config
from src.core.event_bus import EventBus

settings = obtener_config()

async def get_redis() -> Redis:
    """Dependencia para obtener conexión Redis"""
    redis = await from_url(settings.redis_url, decode_responses=False)
    return redis

async def get_event_bus(redis: Redis = Depends(get_redis)) -> EventBus:
    """Dependencia para obtener Event Bus"""
    return EventBus(redis)
