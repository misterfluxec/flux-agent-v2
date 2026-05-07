# =============================================================================
# FLUXAGENT V2 — CACHE DECORATORS
# =============================================================================
# Decoradores para caché automático con invalidación inteligente
# Soporte para rate limiting, condiciones y serialización
# =============================================================================

import functools
import hashlib
import json
import logging
import asyncio
from typing import Callable, Optional, Any, Union, List
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status

from .client import get_cache_client
from .keys import CacheKeyBuilder

logger = logging.getLogger(__name__)

def cached(
    prefix: str,
    ttl: int = 300,
    key_params: Optional[List[str]] = None,
    condition: Optional[Callable[..., bool]] = None,
    serialize_response: bool = True,
    cache_on_error: bool = False,
    invalidate_on: Optional[List[str]] = None
):
    """
    Decorador para cachear respuestas de funciones async.
    
    Args:
        prefix: Prefijo para la clave de cache (ej: "analytics:overview")
        ttl: Tiempo de vida en segundos
        key_params: Parámetros a incluir en la clave (None = todos los kwargs)
        condition: Función que decide si cachear o no
        serialize_response: Si True, serializa respuestas Pydantic automáticamente
        cache_on_error: Si True, cachea también las excepciones
        invalidate_on: Lista de eventos que invalidan este cache
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_client()
            await cache.connect()
            
            # Evaluar condición si existe
            if condition and not condition(*args, **kwargs):
                logger.debug(f"🚫 Cache saltado por condición: {func.__name__}")
                return await func(*args, **kwargs)
            
            # Generar clave de cache
            key_builder = CacheKeyBuilder(prefix, func.__name__)
            if key_params:
                filtered_kwargs = {k: kwargs[k] for k in key_params if k in kwargs}
                cache_key = key_builder.build(**filtered_kwargs)
            else:
                cache_key = key_builder.build(**kwargs)
            
            # Intentar obtener de cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Cache HIT: {cache_key}")
                return cached_result
            
            # Ejecutar función
            logger.debug(f"⚡ Cache MISS: {cache_key}")
            start_time = datetime.now()
            
            try:
                result = await func(*args, **kwargs)
                
                # Cachear resultado exitoso
                if result is not None or cache_on_error:
                    await cache.set(cache_key, result, ttl=ttl)
                
                # Log de performance
                duration = (datetime.now() - start_time).total_seconds()
                logger.debug(f"⏱️ {func.__name__} ejecutado en {duration:.3f}s")
                
                return result
                
            except Exception as e:
                # Cachear error si está habilitado
                if cache_on_error:
                    error_data = {
                        "error": str(e),
                        "type": type(e).__name__,
                        "timestamp": datetime.now().isoformat()
                    }
                    await cache.set(cache_key, error_data, ttl=ttl // 2)  # TTL más corto para errores
                
                raise
        
        # Metadata para invalidación
        wrapper._cache_prefix = prefix
        wrapper._cache_key_params = key_params
        wrapper._invalidate_on = invalidate_on or []
        
        return wrapper
    return decorator


def invalidate_cache(pattern: str, tenant_aware: bool = True):
    """
    Decorador para invalidar cache después de una operación de escritura.
    
    Args:
        pattern: Patrón de claves a eliminar (ej: "analytics:*:tenant_{tenant_id}")
        tenant_aware: Si True, reemplaza {tenant_id} automáticamente
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            # Invalidar cache después de operación exitosa
            cache = get_cache_client()
            await cache.connect()
            
            # Reemplazar placeholders en el patrón
            pattern_resolved = pattern
            if tenant_aware and 'tenant_id' in kwargs:
                pattern_resolved = pattern_resolved.format(tenant_id=kwargs['tenant_id'])
            
            # Agregar más placeholders según necesites
            if '{user_id}' in pattern_resolved and 'user_id' in kwargs:
                pattern_resolved = pattern_resolved.format(user_id=kwargs['user_id'])
            
            deleted = await cache.delete(pattern_resolved)
            if deleted > 0:
                logger.info(f"🗑️ Cache invalidado: {pattern_resolved} ({deleted} claves)")
            
            return result
        return wrapper
    return decorator


def rate_limited_cache(
    prefix: str, 
    window_seconds: int, 
    max_requests: int,
    per_user: bool = True,
    per_tenant: bool = False
):
    """
    Decorador híbrido: cache + rate limiting para endpoints.
    
    Args:
        prefix: Prefijo para cache y rate limit
        window_seconds: Ventana de tiempo para rate limiting
        max_requests: Máximo de requests permitidos
        per_user: Si True, limita por usuario
        per_tenant: Si True, limita por tenant
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_client()
            await cache.connect()
            
            # Determinar identificador para rate limiting
            client_id = 'anonymous'
            if per_user and 'user_id' in kwargs:
                client_id = f"user_{kwargs['user_id']}"
            elif per_tenant and 'tenant_id' in kwargs:
                client_id = f"tenant_{kwargs['tenant_id']}"
            elif 'usuario' in kwargs and hasattr(kwargs['usuario'], 'id'):
                client_id = f"user_{kwargs['usuario'].id}"
            elif 'usuario' in kwargs and hasattr(kwargs['usuario'], 'tenant_id'):
                client_id = f"tenant_{kwargs['usuario'].tenant_id}"
            
            # Rate limit key
            rate_key = f"ratelimit:{prefix}:{client_id}"
            
            # Verificar límite
            current = await cache.increment(rate_key, ttl=window_seconds)
            if current > max_requests:
                logger.warning(f"🚫 Rate limit excedido: {client_id} ({current}/{max_requests})")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit excedido: {max_requests} requests cada {window_seconds}s",
                    headers={
                        "X-RateLimit-Limit": str(max_requests),
                        "X-RateLimit-Remaining": str(max(0, max_requests - current)),
                        "X-RateLimit-Reset": str(window_seconds)
                    }
                )
            
            # Cache normal
            cache_key = f"cache:{prefix}:{client_id}"
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Rate-limited cache HIT: {cache_key}")
                return cached_result
            
            # Ejecutar y cachear
            result = await func(*args, **kwargs)
            cache_ttl = min(window_seconds // 2, 300)  # Cache más corto que rate limit
            await cache.set(cache_key, result, ttl=cache_ttl)
            
            return result
        return wrapper
    return decorator


def smart_cache(
    prefix: str,
    ttl: int = 300,
    strategy: str = "adaptive",  # "adaptive", "write_through", "write_behind"
    hit_ratio_threshold: float = 0.7,
    max_ttl: int = 3600,
    min_ttl: int = 60
):
    """
    Cache inteligente que adapta TTL basado en hit ratio.
    
    Args:
        prefix: Prefijo para cache
        ttl: TTL inicial
        strategy: Estrategia de cache
        hit_ratio_threshold: Umbral para ajustar TTL
        max_ttl: TTL máximo permitido
        min_ttl: TTL mínimo permitido
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_client()
            await cache.connect()
            
            key_builder = CacheKeyBuilder(prefix, func.__name__)
            cache_key = key_builder.build(**kwargs)
            
            # Obtener estadísticas actuales
            stats = cache.get_stats()
            current_hit_ratio = stats.hit_rate
            
            # Ajustar TTL basado en hit ratio
            if strategy == "adaptive":
                if current_hit_ratio > hit_ratio_threshold:
                    # Buen hit ratio: aumentar TTL
                    new_ttl = min(ttl * 1.5, max_ttl)
                else:
                    # Mal hit ratio: reducir TTL
                    new_ttl = max(ttl * 0.7, min_ttl)
            else:
                new_ttl = ttl
            
            # Intentar obtener de cache
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"🎯 Smart cache HIT: {cache_key} (TTL: {new_ttl}s)")
                return cached_result
            
            # Ejecutar y cachear con TTL ajustado
            logger.debug(f"⚡ Smart cache MISS: {cache_key} (TTL: {new_ttl}s)")
            result = await func(*args, **kwargs)
            
            if result is not None:
                await cache.set(cache_key, result, ttl=new_ttl)
            
            return result
        return wrapper
    return decorator


def cache_warmup(
    prefix: str,
    warmup_keys: List[dict],
    ttl: int = 300
):
    """
    Decorador que precarga cache con datos comunes.
    
    Args:
        prefix: Prefijo para cache
        warmup_keys: Lista de diccionarios con parámetros para precargar
        ttl: TTL para datos precargados
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_client()
            await cache.connect()
            
            # Precargar cache si está vacío
            for key_params in warmup_keys:
                key_builder = CacheKeyBuilder(prefix, func.__name__)
                cache_key = key_builder.build(**key_params)
                
                # Solo precargar si no existe
                if not await cache.exists(cache_key):
                    try:
                        result = await func(**key_params)
                        if result is not None:
                            await cache.set(cache_key, result, ttl=ttl)
                            logger.debug(f"🔥 Cache warmed up: {cache_key}")
                    except Exception as e:
                        logger.warning(f"Error en warmup de cache {cache_key}: {e}")
            
            # Ejecutar request normal
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# Helper functions para invalidación masiva
async def invalidate_tenant_cache(tenant_id: str, patterns: Optional[List[str]] = None):
    """Invalida todo el cache de un tenant"""
    cache = get_cache_client()
    await cache.connect()
    
    default_patterns = [
        f"*:tenant_{tenant_id}",
        f"*:{tenant_id}",
        f"tenant:{tenant_id}:*"
    ]
    
    patterns_to_invalidate = patterns or default_patterns
    
    total_deleted = 0
    for pattern in patterns_to_invalidate:
        deleted = await cache.delete(pattern)
        total_deleted += deleted
        logger.info(f"🗑️ Cache invalidado: {pattern} ({deleted} claves)")
    
    return total_deleted


async def invalidate_user_cache(user_id: str, patterns: Optional[List[str]] = None):
    """Invalida cache de un usuario específico"""
    cache = get_cache_client()
    await cache.connect()
    
    default_patterns = [
        f"*:user_{user_id}",
        f"user:{user_id}:*"
    ]
    
    patterns_to_invalidate = patterns or default_patterns
    
    total_deleted = 0
    for pattern in patterns_to_invalidate:
        deleted = await cache.delete(pattern)
        total_deleted += deleted
        logger.info(f"🗑️ Cache usuario invalidado: {pattern} ({deleted} claves)")
    
    return total_deleted


# Decorador para monitoreo de cache
def cache_monitor(prefix: str):
    """Decorador para monitorear performance de cache"""
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_client()
            await cache.connect()
            
            # Estadísticas antes
            stats_before = cache.get_stats()
            
            # Ejecutar función
            start_time = datetime.now()
            result = await func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            
            # Estadísticas después
            stats_after = cache.get_stats()
            
            # Log de monitoreo
            logger.info(
                f"📊 Cache Monitor [{prefix}]: "
                f"Duration: {duration:.3f}s, "
                f"Hits: {stats_after.hits - stats_before.hits}, "
                f"Misses: {stats_after.misses - stats_before.misses}, "
                f"Hit Rate: {stats_after.hit_rate:.2%}"
            )
            
            return result
        return wrapper
    return decorator
