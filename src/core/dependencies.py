from fastapi import Depends, Request
from redis.asyncio import Redis

from core.event_bus import EventBus


async def get_redis(request: Request) -> Redis:
    """Retorna el pool singleton de Redis desde app.state.
    El pool se inicializa en el lifespan de main.py — una sola
    instancia compartida para todo el ciclo de vida del servidor.
    """
    return request.app.state.redis


async def get_event_bus(redis: Redis = Depends(get_redis)) -> EventBus:
    """Dependencia para obtener Event Bus"""
    return EventBus(redis)
