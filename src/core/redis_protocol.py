# =============================================================================
# FLUXAGENT V2 — REDIS PROTOCOL (SEAM EXPLÍCITO)
# =============================================================================
# En lugar de redis_client = None disperso por el proyecto, este módulo define
# un protocolo explícito y un adaptador NullRedis para modo degradado.
#
# Uso:
#   - En producción: lifecycle.py inyecta Redis real vía app.state.redis
#   - En tests/degraded: NullRedis — sin `if redis != None` por todo el proyecto
#
# Arquitectura: RedisProtocol es el SEAM. Redis real y NullRedis son ADAPTADORES.
# =============================================================================

from __future__ import annotations

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RedisProtocol:
    """
    Protocolo mínimo de Redis para FluxAgent.

    Define la interfaz que cualquier adaptador debe satisfacer.
    Permite cambiar implementaciones (real, null, mock, test) sin tocar callers.
    """

    async def get(self, key: str) -> Optional[str]:
        raise NotImplementedError

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        raise NotImplementedError

    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        raise NotImplementedError

    async def delete(self, *keys: str) -> int:
        raise NotImplementedError

    async def exists(self, *keys: str) -> int:
        raise NotImplementedError

    async def incr(self, key: str) -> int:
        raise NotImplementedError

    async def expire(self, key: str, seconds: int) -> bool:
        raise NotImplementedError

    async def publish(self, channel: str, message: str) -> int:
        raise NotImplementedError

    async def ping(self) -> bool:
        raise NotImplementedError

    async def hget(self, name: str, key: str) -> Optional[str]:
        raise NotImplementedError

    async def hset(self, name: str, key: str, value: Any) -> int:
        raise NotImplementedError

    async def hgetall(self, name: str) -> dict:
        raise NotImplementedError

    def pubsub(self):
        raise NotImplementedError

    def lock(self, name: str, timeout: Optional[int] = None, **kwargs):
        raise NotImplementedError


class NullRedis(RedisProtocol):
    """
    Adaptador nulo — explícito y rastreable.

    No falla silenciosamente: loguea cada operación en WARNING para que sea
    visible cuando el sistema corre en modo degradado.

    Úsalo solo durante startup o en tests aislados.
    NO lo uses como fallback permanente en producción.
    """

    def __init__(self):
        logger.warning(
            "⚠️ NullRedis is_active — todas las operaciones Redis son no-ops. "
            "El sistema corre en MODO DEGRADADO. Locks, eventos y caché desactivados."
        )

    async def get(self, key: str) -> None:
        return None

    async def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        return False

    async def setex(self, key: str, seconds: int, value: Any) -> bool:
        return False

    async def delete(self, *keys: str) -> int:
        return 0

    async def exists(self, *keys: str) -> int:
        return 0

    async def incr(self, key: str) -> int:
        return 0

    async def expire(self, key: str, seconds: int) -> bool:
        return False

    async def publish(self, channel: str, message: str) -> int:
        return 0

    async def ping(self) -> bool:
        return False

    async def hget(self, name: str, key: str) -> None:
        return None

    async def hset(self, name: str, key: str, value: Any) -> int:
        return 0

    async def hgetall(self, name: str) -> dict:
        return {}

    def pubsub(self):
        return _NullPubSub()

    def lock(self, name: str, timeout: Optional[int] = None, **kwargs):
        return _NullLock(name)


class _NullPubSub:
    """PubSub no-op para NullRedis."""

    async def subscribe(self, *channels): pass
    async def unsubscribe(self, *channels): pass
    async def get_message(self, **kwargs): return None
    async def close(self): pass


class _NullLock:
    """Lock no-op para NullRedis — no bloquea, siempre 'adquiere'."""

    def __init__(self, name: str):
        logger.warning(f"⚠️ NullLock: lock '{name}' sin backend real — sin protección distribuida.")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def acquire(self, **kwargs) -> bool:
        return True

    async def release(self): pass
