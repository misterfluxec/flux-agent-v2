# =============================================================================
# FLUXAGENT V2 — REDIS CACHE CLIENT
# =============================================================================
# Cliente Redis con serialización Pydantic y manejo de errores resiliente
# Soporte para fallback, retry y métricas
# =============================================================================

import json
import logging
import asyncio
from typing import Optional, Any, TypeVar, Callable, Union, Dict
from datetime import timedelta, datetime
import redis.asyncio as aioredis
from pydantic import BaseModel
from dataclasses import dataclass

from config import obtener_config

logger = logging.getLogger(__name__)
T = TypeVar('T')

@dataclass
class CacheStats:
    """Estadísticas del cache para monitoreo"""
    hits: int = 0
    misses: int = 0
    errors: int = 0
    sets: int = 0
    deletes: int = 0
    
    @property
    def hit_rate(self) -> float:
        """Tasa de hits (0-1)"""
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

class CacheClient:
    """Cliente Redis con serialización Pydantic y manejo de errores resiliente"""
    
    def __init__(self, redis_url: str, default_ttl: int = 300, max_retries: int = 3):
        self.redis: Optional[aioredis.Redis] = None
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.max_retries = max_retries
        self._connected = False
        self._connection_lock = asyncio.Lock()
        self.stats = CacheStats()
        
        # Callbacks para métricas
        self.on_hit: Optional[Callable] = None
        self.on_miss: Optional[Callable] = None
        self.on_error: Optional[Callable] = None
    
    async def connect(self):
        """Conexión lazy con retry exponencial"""
        if self._connected:
            return
        
        async with self._connection_lock:
            if self._connected:
                return
                
            for attempt in range(self.max_retries):
                try:
                    self.redis = aioredis.from_url(
                        self.redis_url, 
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True,
                        health_check_interval=30,
                        max_connections=20
                    )
                    await self.redis.ping()
                    self._connected = True
                    logger.info(f"✅ Redis cache conectado (intento {attempt + 1})")
                    return
                    
                except Exception as e:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"⚠️ Intento {attempt + 1} fallido conectando Redis: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(wait_time)
            
            logger.error(f"❌ No se pudo conectar a Redis después de {self.max_retries} attempts")
            self._connected = False
    
    async def close(self):
        """Cierra conexión de forma segura"""
        if self.redis and self._connected:
            try:
                await self.redis.aclose()
            except Exception as e:
                logger.warning(f"Error cerrando Redis: {e}")
            finally:
                self._connected = False
    
    async def health_check(self) -> bool:
        """Verifica salud del cache"""
        try:
            if not self._connected or not self.redis:
                return False
            await self.redis.ping()
            return True
        except Exception:
            return False
    
    async def get(self, key: str, model: Optional[type[T]] = None) -> Optional[T]:
        """Obtener valor con deserialización opcional a Pydantic"""
        if not self._connected or not self.redis:
            self.stats.misses += 1
            if self.on_miss:
                await self._safe_call(self.on_miss, key)
            return None
        
        try:
            data = await self.redis.get(key)
            if data is None:
                self.stats.misses += 1
                if self.on_miss:
                    await self._safe_call(self.on_miss, key)
                return None
            
            # Deserialización
            if model and issubclass(model, BaseModel):
                result = model.model_validate_json(data)
            else:
                result = json.loads(data) if isinstance(data, str) else data
            
            self.stats.hits += 1
            if self.on_hit:
                await self._safe_call(self.on_hit, key, result)
            
            logger.debug(f"🎯 Cache HIT: {key}")
            return result
            
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "get", key, e)
            logger.error(f"Error leyendo cache {key}: {e}")
            return None  # Fail-open: no romper la app si cache falla
    
    async def set(
        self, 
        key: str, 
        value: Any, 
        ttl: Optional[int] = None,
        nx: bool = False,  # Solo setear si no existe
        xx: bool = False   # Solo setear si existe
    ) -> bool:
        """Setear valor con serialización automática"""
        if not self._connected or not self.redis:
            return False
        
        try:
            # Serialización
            serialized = self._serialize_value(value)
            ttl = ttl or self.default_ttl
            
            result = await self.redis.set(key, serialized, ex=ttl, nx=nx, xx=xx)
            self.stats.sets += 1
            
            logger.debug(f"💾 Cache SET: {key} (TTL: {ttl}s)")
            return bool(result)
            
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "set", key, e)
            logger.error(f"Error escribiendo cache {key}: {e}")
            return False
    
    async def delete(self, pattern: str) -> int:
        """Eliminar claves por patrón (para invalidación)"""
        if not self._connected or not self.redis:
            return 0
        
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                deleted = await self.redis.delete(*keys)
                self.stats.deletes += deleted
                logger.debug(f"🗑️ Cache DELETE: {pattern} ({deleted} claves)")
                return deleted
            return 0
            
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "delete", pattern, e)
            logger.error(f"Error eliminando cache {pattern}: {e}")
            return 0
    
    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Incremento atómico para rate limiting / contadores"""
        if not self._connected or not self.redis:
            return 0
        
        try:
            result = await self.redis.incr(key, amount)
            if ttl and result == amount:  # Solo setear TTL si es primera vez
                await self.redis.expire(key, ttl)
            logger.debug(f"📈 Cache INCR: {key} (+{amount}) = {result}")
            return result
            
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "increment", key, e)
            logger.error(f"Error incrementando {key}: {e}")
            return 0
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Setear TTL a clave existente"""
        if not self._connected or not self.redis:
            return False
        
        try:
            result = await self.redis.expire(key, ttl)
            logger.debug(f"⏰ Cache EXPIRE: {key} ({ttl}s)")
            return bool(result)
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "expire", key, e)
            logger.error(f"Error seteando TTL {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Verificar si clave existe"""
        if not self._connected or not self.redis:
            return False
        
        try:
            result = await self.redis.exists(key)
            return bool(result)
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "exists", key, e)
            logger.error(f"Error verificando existencia {key}: {e}")
            return False
    
    async def get_ttl(self, key: str) -> int:
        """Obtener TTL de clave (-1 si no expira, -2 si no existe)"""
        if not self._connected or not self.redis:
            return -2
        
        try:
            return await self.redis.ttl(key)
        except Exception as e:
            self.stats.errors += 1
            if self.on_error:
                await self._safe_call(self.on_error, "ttl", key, e)
            logger.error(f"Error obteniendo TTL {key}: {e}")
            return -2
    
    def get_stats(self) -> CacheStats:
        """Obtener estadísticas del cache"""
        return self.stats
    
    def reset_stats(self):
        """Resetear estadísticas"""
        self.stats = CacheStats()
    
    def _serialize_value(self, value: Any) -> str:
        """Serializa valor a JSON"""
        if isinstance(value, BaseModel):
            return value.model_dump_json()
        elif isinstance(value, (dict, list)):
            return json.dumps(value, default=str)
        elif isinstance(value, (datetime, timedelta)):
            return str(value)
        else:
            return str(value)
    
    async def _safe_call(self, callback: Callable, *args, **kwargs):
        """Ejecuta callback de forma segura"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Error en callback de cache: {e}")

# Singleton global con lazy initialization
_cache_client: Optional[CacheClient] = None

def get_cache_client() -> CacheClient:
    """Obtiene cliente cache singleton"""
    global _cache_client
    if _cache_client is None:
        config = obtener_config()
        _cache_client = CacheClient(
            redis_url=config.redis_url,
            default_ttl=300,
            max_retries=3
        )
    return _cache_client

async def initialize_cache():
    """Inicializa cache al iniciar la aplicación"""
    cache = get_cache_client()
    await cache.connect()
    logger.info("🚀 Cache inicializado")

async def cleanup_cache():
    """Limpia cache al cerrar la aplicación"""
    cache = get_cache_client()
    await cache.close()
    logger.info("🧹 Cache limpiado")
