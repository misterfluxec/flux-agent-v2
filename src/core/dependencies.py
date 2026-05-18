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

# =============================================================================
# SEGURIDAD WEBHOOKS (HMAC) Y RATE LIMITING (Fase 1 Enterprise)
# =============================================================================
import hmac
import hashlib
import asyncio
from uuid import uuid4
from fastapi import HTTPException
from config import obtener_config

config = obtener_config()

async def verify_evolution_signature(request: Request):
    """Validación HMAC-SHA256 para Webhooks de Evolution API"""
    signature = request.headers.get("webhook-signature")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing webhook signature")
    
    raw_body = await request.body()
    expected = hmac.new(
        config.evolution_webhook_secret.encode(),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")
    return True

async def verify_mp_signature(request: Request, x_signature: str = None, x_request_id: str = None):
    """Validación HMAC-SHA256 para Webhooks de MercadoPago"""
    if not config.mp_webhook_secret:
        return True  # Permitir en dev si no está configurado
    
    manifest = f"id:{request.query_params.get('id', '')};request-id:{x_request_id};"
    expected = hmac.new(
        config.mp_webhook_secret.encode(),
        manifest.encode(),
        hashlib.sha256
    ).hexdigest()
    
    if not hmac.compare_digest(expected, x_signature):
        raise HTTPException(status_code=403, detail="Invalid MercadoPago signature")
    return True

async def rate_limit_per_tenant(request: Request, redis: Redis = Depends(get_redis)):
    """Rate Limiting Multi-Tenant basado en Sliding Window sobre Redis"""
    tenant_id = request.headers.get("X-Tenant-ID") or getattr(request.state, "tenant_id", "unknown")
    endpoint = request.url.path
    key = f"rl:{tenant_id}:{endpoint}"
    
    now = int(asyncio.get_event_loop().time())
    window = 60  # 1 minuto
    limit = 100  # requests/min
    
    pipeline = redis.pipeline()
    pipeline.zremrangebyscore(key, 0, now - window)
    pipeline.zadd(key, {f"{now}:{uuid4()}": now})
    pipeline.zcard(key)
    pipeline.expire(key, window + 10)
    
    results = await pipeline.execute()
    current = results[2]
    
    if current > limit:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
