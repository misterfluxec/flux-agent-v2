# =============================================================================
# FLUXAGENT V2 — ASYNC RETRY MECHANISM
# =============================================================================
# Sistema de reintentos con backoff exponencial y jitter
# Protección contra fallos transitorios con configuración flexible
# =============================================================================

import asyncio
import logging
import random
import time
from typing import Callable, Any, Optional, List, Type, Union
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class BackoffStrategy(Enum):
    """Estrategias de backoff para reintentos"""
    FIXED = "fixed"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_WITH_JITTER = "exponential_with_jitter"
    EXPONENTIAL_WITH_FULL_JITTER = "exponential_with_full_jitter"

@dataclass
class RetryConfig:
    """Configuración del mecanismo de retry"""
    max_attempts: int = 3
    base_delay: float = 1.0  # Segundos base
    max_delay: float = 60.0  # Máximo delay
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_WITH_JITTER
    jitter: bool = True  # Agregar variación aleatoria
    multiplier: float = 2.0  # Multiplicador para exponencial
    retryable_exceptions: List[Type[Exception]] = None
    non_retryable_exceptions: List[Type[Exception]] = None
    on_retry_callback: Optional[Callable] = None
    on_give_up_callback: Optional[Callable] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [Exception]
        if self.non_retryable_exceptions is None:
            self.non_retryable_exceptions = []

class RetryState:
    """Estado actual del mecanismo de retry"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempt = 0
        self.total_delay = 0.0
        self.exceptions: List[Exception] = []
        self.start_time = time.time()
    
    def should_retry(self, exception: Exception) -> bool:
        """Determina si se debe reintentar"""
        if self.attempt >= self.config.max_attempts:
            return False
        
        # Verificar si la excepción es no reintentable
        for non_retryable in self.config.non_retryable_exceptions:
            if isinstance(exception, non_retryable):
                return False
        
        # Verificar si la excepción es reintentable
        for retryable in self.config.retryable_exceptions:
            if isinstance(exception, retryable):
                return True
        
        return False
    
    def calculate_delay(self) -> float:
        """Calcula delay según estrategia de backoff"""
        if self.config.backoff_strategy == BackoffStrategy.FIXED:
            delay = self.config.base_delay
            
        elif self.config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = self.config.base_delay * self.attempt
            
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.multiplier ** (self.attempt - 1))
            
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL_WITH_JITTER:
            base_delay = self.config.base_delay * (self.config.multiplier ** (self.attempt - 1))
            jitter_range = base_delay * 0.1  # 10% jitter
            delay = base_delay + random.uniform(-jitter_range, jitter_range)
            
        elif self.config.backoff_strategy == BackoffStrategy.EXPONENTIAL_WITH_FULL_JITTER:
            base_delay = self.config.base_delay * (self.config.multiplier ** (self.attempt - 1))
            delay = random.uniform(0, base_delay)
            
        else:
            delay = self.config.base_delay
        
        # Aplicar jitter adicional si está habilitado
        if self.config.jitter and self.config.backoff_strategy != BackoffStrategy.EXPONENTIAL_WITH_FULL_JITTER:
            jitter_range = delay * 0.1
            delay += random.uniform(-jitter_range, jitter_range)
        
        # Limitar al máximo
        return min(delay, self.config.max_delay)
    
    def record_attempt(self, exception: Exception):
        """Registra un intento fallido"""
        self.attempt += 1
        self.exceptions.append(exception)
    
    def get_stats(self) -> dict:
        """Retorna estadísticas del retry"""
        return {
            "attempts": self.attempt,
            "max_attempts": self.config.max_attempts,
            "total_delay": self.total_delay,
            "elapsed_time": time.time() - self.start_time,
            "exceptions": [str(e) for e in self.exceptions],
            "success": self.attempt == 0 or (self.attempt > 0 and len(self.exceptions) < self.attempt)
        }

class AsyncRetry:
    """Mecanismo de retry asíncrono avanzado"""
    
    def __init__(self, config: RetryConfig):
        self.config = config
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función con reintentos"""
        state = RetryState(self.config)
        
        while True:
            try:
                # Primer intento o reintento
                if state.attempt == 0:
                    result = await func(*args, **kwargs)
                    logger.debug(f"Retry succeeded on first attempt: {func.__name__}")
                    return result
                else:
                    delay = state.calculate_delay()
                    state.total_delay += delay
                    
                    logger.info(
                        f"Retry attempt {state.attempt}/{state.config.max_attempts} "
                        f"for {func.__name__} after {delay:.2f}s delay"
                    )
                    
                    # Notificar callback de retry
                    if self.config.on_retry_callback:
                        await self._safe_callback(
                            self.config.on_retry_callback,
                            state.attempt,
                            state.exceptions[-1],
                            delay
                        )
                    
                    await asyncio.sleep(delay)
                    result = await func(*args, **kwargs)
                    
                    logger.info(f"Retry succeeded on attempt {state.attempt}: {func.__name__}")
                    return result
                    
            except Exception as e:
                state.record_attempt(e)
                
                if not state.should_retry(e):
                    # No más reintentos
                    logger.error(
                        f"Retry failed after {state.attempt} attempts: {func.__name__} - {e}"
                    )
                    
                    # Notificar callback de give up
                    if self.config.on_give_up_callback:
                        await self._safe_callback(
                            self.config.on_give_up_callback,
                            state.attempt,
                            state.exceptions,
                            state.get_stats()
                        )
                    
                    raise RetryExhaustedException(
                        f"Failed after {state.attempt} attempts",
                        attempts=state.attempt,
                        exceptions=state.exceptions,
                        stats=state.get_stats()
                    )
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Ejecuta callback de forma segura"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in retry callback: {e}")

def async_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL_WITH_JITTER,
    jitter: bool = True,
    multiplier: float = 2.0,
    retryable_exceptions: List[Type[Exception]] = None,
    non_retryable_exceptions: List[Type[Exception]] = None,
    on_retry_callback: Optional[Callable] = None,
    on_give_up_callback: Optional[Callable] = None
):
    """Decorador para retry asíncrono con configuración flexible"""
    def decorator(func: Callable):
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            max_delay=max_delay,
            backoff_strategy=backoff_strategy,
            jitter=jitter,
            multiplier=multiplier,
            retryable_exceptions=retryable_exceptions,
            non_retryable_exceptions=non_retryable_exceptions,
            on_retry_callback=on_retry_callback,
            on_give_up_callback=on_give_up_callback
        )
        
        retry = AsyncRetry(config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry.execute(func, *args, **kwargs)
        
        # Agregar metadata para debugging
        wrapper._retry_config = config
        wrapper._retry_enabled = True
        
        return wrapper
    
    return decorator

# Configuraciones predefinidas para servicios comunes
RETRY_CONFIGS = {
    "database": RetryConfig(
        max_attempts=3,
        base_delay=0.5,
        max_delay=10.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
        retryable_exceptions=[ConnectionError, TimeoutError]
    ),
    
    "redis": RetryConfig(
        max_attempts=5,
        base_delay=0.1,
        max_delay=5.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
        retryable_exceptions=[ConnectionError, TimeoutError]
    ),
    
    "http_api": RetryConfig(
        max_attempts=3,
        base_delay=1.0,
        max_delay=30.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
        retryable_exceptions=[ConnectionError, TimeoutError]
    ),
    
    "llm": RetryConfig(
        max_attempts=2,
        base_delay=2.0,
        max_delay=60.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
        retryable_exceptions=[ConnectionError, TimeoutError]
    ),
    
    "whatsapp": RetryConfig(
        max_attempts=3,
        base_delay=5.0,
        max_delay=120.0,
        backoff_strategy=BackoffStrategy.EXPONENTIAL_WITH_JITTER,
        retryable_exceptions=[ConnectionError, TimeoutError]
    ),
    
    "voice": RetryConfig(
        max_attempts=2,
        base_delay=1.0,
        max_delay=30.0,
        backoff_strategy=BackoffStrategy.LINEAR,
        retryable_exceptions=[ConnectionError, TimeoutError]
    )
}

def create_retry(service_name: str, **overrides) -> AsyncRetry:
    """Crea mecanismo de retry con configuración predefinida"""
    if service_name not in RETRY_CONFIGS:
        raise ValueError(f"Unknown service: {service_name}")
    
    base_config = RETRY_CONFIGS[service_name]
    
    # Aplicar overrides
    config_dict = {
        "max_attempts": base_config.max_attempts,
        "base_delay": base_config.base_delay,
        "max_delay": base_config.max_delay,
        "backoff_strategy": base_config.backoff_strategy,
        "jitter": base_config.jitter,
        "multiplier": base_config.multiplier,
        "retryable_exceptions": base_config.retryable_exceptions,
        "non_retryable_exceptions": base_config.non_retryable_exceptions,
        **overrides
    }
    
    config = RetryConfig(**config_dict)
    return AsyncRetry(config)

# Excepciones personalizadas
class RetryException(Exception):
    """Base exception para retry mechanism"""
    pass

class RetryExhaustedException(RetryException):
    """Excepción cuando se agotan los reintentos"""
    
    def __init__(self, message: str, attempts: int, exceptions: List[Exception], stats: dict):
        super().__init__(message)
        self.attempts = attempts
        self.exceptions = exceptions
        self.stats = stats

class RetryTimeoutException(RetryException):
    """Excepción cuando hay timeout durante retry"""
    pass

# Utilidades para monitoreo
class RetryMetrics:
    """Métricas del sistema de retry"""
    
    def __init__(self):
        self.total_retries = 0
        self.successful_retries = 0
        self.failed_retries = 0
        self.total_delay = 0.0
        self.service_stats = {}
    
    def record_retry(self, service: str, success: bool, attempts: int, delay: float):
        """Registra estadísticas de retry"""
        self.total_retries += 1
        
        if success:
            self.successful_retries += 1
        else:
            self.failed_retries += 1
        
        self.total_delay += delay
        
        # Estadísticas por servicio
        if service not in self.service_stats:
            self.service_stats[service] = {
                "total": 0,
                "successful": 0,
                "failed": 0,
                "total_delay": 0.0,
                "avg_attempts": 0.0
            }
        
        self.service_stats[service]["total"] += 1
        self.service_stats[service]["total_delay"] += delay
        
        if success:
            self.service_stats[service]["successful"] += 1
        else:
            self.service_stats[service]["failed"] += 1
        
        # Calcular promedio de attempts
        total_service = self.service_stats[service]["total"]
        self.service_stats[service]["avg_attempts"] = (
            self.service_stats[service]["total_delay"] / total_service
            if total_service > 0 else 0.0
        )
    
    def get_stats(self) -> dict:
        """Retorna estadísticas completas"""
        return {
            "global": {
                "total_retries": self.total_retries,
                "successful_retries": self.successful_retries,
                "failed_retries": self.failed_retries,
                "success_rate": self.successful_retries / self.total_retries if self.total_retries > 0 else 0.0,
                "total_delay": self.total_delay,
                "avg_delay": self.total_delay / self.total_retries if self.total_retries > 0 else 0.0
            },
            "by_service": self.service_stats
        }

# Singleton global para métricas
_retry_metrics: Optional[RetryMetrics] = None

def get_retry_metrics() -> RetryMetrics:
    """Obtiene instancia singleton de métricas de retry"""
    global _retry_metrics
    if _retry_metrics is None:
        _retry_metrics = RetryMetrics()
    return _retry_metrics
