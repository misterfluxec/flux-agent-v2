import logging
import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

# En producción, esto se conectaría a un RedisClient real.
# Para esta abstracción inicial y local-testing, simulamos los locks en memoria
# preparándolos para la interfaz asíncrona de Redis (`aioredis`).

logger = logging.getLogger(__name__)

class LockAcquisitionError(Exception):
    """Lanzada cuando no se puede obtener un candado (otra sync está corriendo)."""
    pass

class DistributedLockManager:
    """
    Abstracción para Distributed Locking (Redis).
    Garantiza que una integración (ej. Shopify de la tienda A)
    no ejecute dos sincronizaciones en paralelo.
    """
    _locks_in_memory = set()
    _redis_client = None

    @classmethod
    def set_redis(cls, redis_client):
        """Configura el cliente Redis para usar locks distribuidos reales."""
        cls._redis_client = redis_client

    @classmethod
    @asynccontextmanager
    async def acquire_lock(cls, lock_key: str, timeout_seconds: int = 3600) -> AsyncGenerator[None, None]:
        """
        Adquiere un distributed lock. Falla inmediatamente si ya está tomado.
        """
        if cls._redis_client:
            # Usa Redis distributed lock
            # blocking_timeout=0 significa que falla inmediatamente si está tomado
            lock = cls._redis_client.lock(lock_key, timeout=timeout_seconds, blocking_timeout=0)
            acquired = await lock.acquire()
            if not acquired:
                logger.warning(f"[DistributedLock] No se pudo adquirir el candado en Redis. Ocupado: {lock_key}")
                raise LockAcquisitionError(f"Job ya está en ejecución para la llave: {lock_key}")
            
            logger.debug(f"[DistributedLock] Candado adquirido en Redis: {lock_key}")
            try:
                yield
            finally:
                try:
                    await lock.release()
                except Exception as e:
                    logger.error(f"[DistributedLock] Error liberando lock en Redis: {e}")
                logger.debug(f"[DistributedLock] Candado liberado en Redis: {lock_key}")
        else:
            # Fallback a memoria (para testing local sin Redis configurado)
            if lock_key in cls._locks_in_memory:
                logger.warning(f"[DistributedLock] No se pudo adquirir el candado en memoria. Ocupado: {lock_key}")
                raise LockAcquisitionError(f"Job ya está en ejecución para la llave: {lock_key}")
                
            cls._locks_in_memory.add(lock_key)
            logger.debug(f"[DistributedLock] Candado adquirido en memoria: {lock_key}")
            try:
                yield
            finally:
                cls._locks_in_memory.discard(lock_key)
                logger.debug(f"[DistributedLock] Candado liberado en memoria: {lock_key}")

