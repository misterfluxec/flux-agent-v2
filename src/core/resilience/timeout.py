# =============================================================================
# FLUXAGENT V2 — ASYNC TIMEOUT HANDLING
# =============================================================================
# Sistema de timeouts configurables y con fallback
# Protección contra operaciones que se bloquean indefinidamente
# =============================================================================

import asyncio
import logging
from typing import Callable, Any, Optional, Dict
from functools import wraps
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TimeoutStrategy(Enum):
    """Estrategias de timeout"""
    FIXED = "fixed"                    # Timeout fijo
    ADAPTIVE = "adaptive"              # Timeout adaptativo basado en historial
    EXPONENTIAL_BACKOFF = "exponential" # Timeout con backoff exponencial

@dataclass
class TimeoutConfig:
    """Configuración del timeout"""
    name: str
    timeout: float = 30.0              # Timeout base en segundos
    max_timeout: float = 300.0          # Timeout máximo
    min_timeout: float = 1.0             # Timeout mínimo
    strategy: TimeoutStrategy = TimeoutStrategy.FIXED
    fallback_enabled: bool = True         # Habilitar fallback
    fallback_response: Any = None        # Respuesta fallback
    adaptive_window: int = 100            # Ventana para timeout adaptativo
    jitter: bool = True                  # Agregar jitter al timeout
    on_timeout_callback: Optional[Callable] = None

@dataclass
class TimeoutMetrics:
    """Métricas del timeout"""
    total_calls: int = 0
    successful_calls: int = 0
    timeout_calls: int = 0
    avg_execution_time: float = 0.0
    avg_timeout_used: float = 0.0
    last_execution_time: Optional[float] = None
    last_timeout_used: Optional[float] = None
    execution_times: list = None
    
    def __post_init__(self):
        if self.execution_times is None:
            self.execution_times = []
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito (0-1)"""
        total = self.total_calls
        return self.successful_calls / total if total > 0 else 0.0
    
    @property
    def timeout_rate(self) -> float:
        """Tasa de timeouts (0-1)"""
        total = self.total_calls
        return self.timeout_calls / total if total > 0 else 0.0

class AsyncTimeout:
    """Sistema de timeout asíncrono avanzado"""
    
    def __init__(self, config: TimeoutConfig):
        self.config = config
        self.metrics = TimeoutMetrics()
        self._lock = asyncio.Lock()
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función con protección de timeout"""
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Calcular timeout según estrategia
            timeout = await self._calculate_timeout()
            
            # Ejecutar con timeout
            result = await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout
            )
            
            # Actualizar métricas de éxito
            execution_time = asyncio.get_event_loop().time() - start_time
            await self._on_success(execution_time, timeout)
            
            return result
            
        except asyncio.TimeoutError:
            # Timeout
            execution_time = asyncio.get_event_loop().time() - start_time
            await self._on_timeout(execution_time)
            
            # Fallback o lanzar excepción
            if self.config.fallback_enabled and self.config.fallback_response is not None:
                logger.warning(f"Timeout {self.config.name} - Using fallback")
                return self.config.fallback_response
            else:
                raise TimeoutException(f"Timeout in {self.config.name} after {timeout}s")
        
        except Exception as e:
            # Error inesperado
            execution_time = asyncio.get_event_loop().time() - start_time
            await self._on_error(execution_time, e)
            raise
    
    async def _calculate_timeout(self) -> float:
        """Calcula timeout según estrategia"""
        if self.config.strategy == TimeoutStrategy.FIXED:
            timeout = self.config.timeout
            
        elif self.config.strategy == TimeoutStrategy.ADAPTIVE:
            timeout = await self._adaptive_timeout()
            
        elif self.config.strategy == TimeoutStrategy.EXPONENTIAL_BACKOFF:
            timeout = await self._exponential_backoff_timeout()
            
        else:
            timeout = self.config.timeout
        
        # Aplicar jitter si está habilitado
        if self.config.jitter:
            import random
            jitter_range = timeout * 0.1  # 10% jitter
            timeout += random.uniform(-jitter_range, jitter_range)
        
        # Limitar al rango permitido
        return max(self.config.min_timeout, min(timeout, self.config.max_timeout))
    
    async def _adaptive_timeout(self) -> float:
        """Calcula timeout adaptativo basado en historial"""
        async with self._lock:
            if len(self.metrics.execution_times) < 5:
                return self.config.timeout
            
            # Calcular promedio de ejecuciones recientes
            recent_times = self.metrics.execution_times[-self.config.adaptive_window:]
            avg_time = sum(recent_times) / len(recent_times)
            
            # Ajustar timeout basado en el promedio
            if self.metrics.timeout_rate > 0.1:  # Más del 10% de timeouts
                # Aumentar timeout
                timeout = avg_time * 1.5
            else:
                # Reducir timeout gradualmente
                timeout = avg_time * 1.1
            
            return timeout
    
    async def _exponential_backoff_timeout(self) -> float:
        """Calcula timeout con backoff exponencial"""
        async with self._lock:
            # Calcular timeout basado en tasa de timeouts reciente
            recent_timeouts = sum(1 for t in self.metrics.execution_times[-10:] 
                                if t > self.config.timeout)
            
            if recent_timeouts == 0:
                return self.config.timeout
            
            # Backoff exponencial basado en timeouts consecutivos
            backoff_factor = min(2 ** recent_timeouts, 10)  # Máximo 10x
            timeout = self.config.timeout * backoff_factor
            
            return timeout
    
    async def _on_success(self, execution_time: float, timeout_used: float):
        """Maneja llamada exitosa"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.successful_calls += 1
            self.metrics.last_execution_time = execution_time
            self.metrics.last_timeout_used = timeout_used
            
            # Actualizar historial de tiempos
            self.metrics.execution_times.append(execution_time)
            if len(self.metrics.execution_times) > self.config.adaptive_window:
                self.metrics.execution_times = self.metrics.execution_times[-self.config.adaptive_window:]
            
            # Recalcular promedios
            if self.metrics.execution_times:
                self.metrics.avg_execution_time = sum(self.metrics.execution_times) / len(self.metrics.execution_times)
                self.metrics.avg_timeout_used = timeout_used
            
            # Callback de éxito
            if self.config.on_timeout_callback:
                await self._safe_callback(
                    self.config.on_timeout_callback,
                    "success",
                    execution_time,
                    timeout_used
                )
        
        logger.debug(f"Timeout {self.config.name}: SUCCESS ({execution_time:.3f}s)")
    
    async def _on_timeout(self, execution_time: float):
        """Maneja timeout"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.timeout_calls += 1
            self.metrics.last_execution_time = execution_time
            
            # Callback de timeout
            if self.config.on_timeout_callback:
                await self._safe_callback(
                    self.config.on_timeout_callback,
                    "timeout",
                    execution_time
                )
        
        logger.warning(f"Timeout {self.config.name}: TIMEOUT ({execution_time:.3f}s)")
    
    async def _on_error(self, execution_time: float, error: Exception):
        """Maneja error inesperado"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.last_execution_time = execution_time
        
        logger.error(f"Timeout {self.config.name}: ERROR ({execution_time:.3f}s) - {error}")
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Ejecuta callback de forma segura"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in timeout callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status actual y métricas"""
        return {
            "name": self.config.name,
            "config": {
                "timeout": self.config.timeout,
                "max_timeout": self.config.max_timeout,
                "min_timeout": self.config.min_timeout,
                "strategy": self.config.strategy.value,
                "fallback_enabled": self.config.fallback_enabled
            },
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "timeout_calls": self.metrics.timeout_calls,
                "success_rate": self.metrics.success_rate,
                "timeout_rate": self.metrics.timeout_rate,
                "avg_execution_time": self.metrics.avg_execution_time,
                "avg_timeout_used": self.metrics.avg_timeout_used,
                "last_execution_time": self.metrics.last_execution_time,
                "last_timeout_used": self.metrics.last_timeout_used
            }
        }
    
    async def reset_metrics(self):
        """Resetea métricas"""
        async with self._lock:
            self.metrics = TimeoutMetrics()

# Diccionario global para instancias
_timeouts: Dict[str, AsyncTimeout] = {}

def get_timeout(name: str, config: Optional[TimeoutConfig] = None) -> AsyncTimeout:
    """Obtiene o crea instancia de timeout"""
    if name not in _timeouts:
        if config is None:
            raise ValueError(f"Timeout '{name}' not found and no config provided")
        _timeouts[name] = AsyncTimeout(config)
    return _timeouts[name]

def async_timeout(
    name: str,
    timeout: float = 30.0,
    max_timeout: float = 300.0,
    min_timeout: float = 1.0,
    strategy: TimeoutStrategy = TimeoutStrategy.FIXED,
    fallback_enabled: bool = False,
    fallback_response: Any = None,
    adaptive_window: int = 100,
    jitter: bool = True,
    on_timeout_callback: Optional[Callable] = None
):
    """Decorador para proteger funciones asíncronas con timeout"""
    def decorator(func: Callable):
        config = TimeoutConfig(
            name=name,
            timeout=timeout,
            max_timeout=max_timeout,
            min_timeout=min_timeout,
            strategy=strategy,
            fallback_enabled=fallback_enabled,
            fallback_response=fallback_response,
            adaptive_window=adaptive_window,
            jitter=jitter,
            on_timeout_callback=on_timeout_callback
        )
        
        timeout_handler = get_timeout(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await timeout_handler.execute(func, *args, **kwargs)
        
        # Agregar metadata para debugging
        wrapper._timeout_name = name
        wrapper._timeout_config = config
        
        return wrapper
    
    return decorator

# Configuraciones predefinidas para servicios comunes
TIMEOUT_CONFIGS = {
    "database": TimeoutConfig(
        name="database",
        timeout=10.0,
        max_timeout=60.0,
        min_timeout=0.5,
        strategy=TimeoutStrategy.ADAPTIVE,
        fallback_enabled=False
    ),
    
    "redis": TimeoutConfig(
        name="redis",
        timeout=5.0,
        max_timeout=30.0,
        min_timeout=0.1,
        strategy=TimeoutStrategy.FIXED,
        fallback_enabled=False
    ),
    
    "http_api": TimeoutConfig(
        name="http_api",
        timeout=30.0,
        max_timeout=120.0,
        min_timeout=1.0,
        strategy=TimeoutStrategy.EXPONENTIAL_BACKOFF,
        fallback_enabled=True,
        fallback_response={"error": "API timeout"}
    ),
    
    "llm": TimeoutConfig(
        name="llm",
        timeout=60.0,
        max_timeout=300.0,
        min_timeout=5.0,
        strategy=TimeoutStrategy.ADAPTIVE,
        fallback_enabled=True,
        fallback_response={"error": "LLM timeout"}
    ),
    
    "whatsapp": TimeoutConfig(
        name="whatsapp",
        timeout=15.0,
        max_timeout=60.0,
        min_timeout=1.0,
        strategy=TimeoutStrategy.EXPONENTIAL_BACKOFF,
        fallback_enabled=True,
        fallback_response={"error": "WhatsApp timeout"}
    ),
    
    "voice": TimeoutConfig(
        name="voice",
        timeout=120.0,
        max_timeout=600.0,
        min_timeout=10.0,
        strategy=TimeoutStrategy.ADAPTIVE,
        fallback_enabled=True,
        fallback_response={"error": "Voice processing timeout"}
    ),
    
    "file_upload": TimeoutConfig(
        name="file_upload",
        timeout=300.0,
        max_timeout=1800.0,
        min_timeout=10.0,
        strategy=TimeoutStrategy.FIXED,
        fallback_enabled=True,
        fallback_response={"error": "File upload timeout"}
    )
}

def create_timeout(service_name: str, **overrides) -> AsyncTimeout:
    """Crea timeout con configuración predefinida y overrides"""
    if service_name not in TIMEOUT_CONFIGS:
        raise ValueError(f"Unknown service: {service_name}")
    
    base_config = TIMEOUT_CONFIGS[service_name]
    
    # Aplicar overrides
    config_dict = {
        "name": base_config.name,
        "timeout": base_config.timeout,
        "max_timeout": base_config.max_timeout,
        "min_timeout": base_config.min_timeout,
        "strategy": base_config.strategy,
        "fallback_enabled": base_config.fallback_enabled,
        "fallback_response": base_config.fallback_response,
        "adaptive_window": base_config.adaptive_window,
        "jitter": base_config.jitter,
        "on_timeout_callback": base_config.on_timeout_callback,
        **overrides
    }
    
    config = TimeoutConfig(**config_dict)
    return AsyncTimeout(config)

# Endpoint para monitoreo de timeouts
async def get_all_timeouts_status() -> Dict[str, Any]:
    """Retorna status de todos los timeouts"""
    status = {}
    for name, timeout in _timeouts.items():
        status[name] = timeout.get_status()
    return status

# Excepciones personalizadas
class TimeoutException(Exception):
    """Excepción base para timeout"""
    pass

class AdaptiveTimeoutException(TimeoutException):
    """Excepción para timeout adaptativo"""
    pass

class ExponentialBackoffTimeoutException(TimeoutException):
    """Excepción para timeout con backoff exponencial"""
    pass

# Utilidades para gestión de timeouts
class TimeoutManager:
    """Gestor para administración de timeouts"""
    
    def __init__(self):
        self.timeouts = _timeouts
    
    def add_timeout(self, timeout: AsyncTimeout):
        """Agrega un timeout al gestor"""
        self.timeouts[timeout.config.name] = timeout
        logger.info(f"Timeout added: {timeout.config.name}")
    
    def remove_timeout(self, name: str) -> bool:
        """Remueve un timeout del gestor"""
        if name in self.timeouts:
            del self.timeouts[name]
            logger.info(f"Timeout removed: {name}")
            return True
        return False
    
    def get_timeout(self, name: str) -> Optional[AsyncTimeout]:
        """Obtiene un timeout por name"""
        return self.timeouts.get(name)
    
    def list_timeouts(self) -> list[str]:
        """Lista todos los timeouts"""
        return list(self.timeouts.keys())
    
    async def reset_all_metrics(self):
        """Resetea métricas de todos los timeouts"""
        for timeout in self.timeouts.values():
            await timeout.reset_metrics()
        logger.info("All timeout metrics reset")
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas globales de todos los timeouts"""
        global_metrics = {
            "total_timeouts": len(self.timeouts),
            "total_calls": 0,
            "successful_calls": 0,
            "timeout_calls": 0,
            "avg_execution_time": 0.0,
            "avg_timeout_rate": 0.0
        }
        
        total_execution_times = []
        for timeout in self.timeouts.values():
            metrics = timeout.metrics
            global_metrics["total_calls"] += metrics.total_calls
            global_metrics["successful_calls"] += metrics.successful_calls
            global_metrics["timeout_calls"] += metrics.timeout_calls
            total_execution_times.extend(metrics.execution_times)
        
        # Calcular promedios globales
        if global_metrics["total_calls"] > 0:
            global_metrics["success_rate"] = (
                global_metrics["successful_calls"] / global_metrics["total_calls"]
            )
            global_metrics["timeout_rate"] = (
                global_metrics["timeout_calls"] / global_metrics["total_calls"]
            )
        
        if total_execution_times:
            global_metrics["avg_execution_time"] = sum(total_execution_times) / len(total_execution_times)
        
        return global_metrics

# Singleton global para el gestor
_timeout_manager: Optional[TimeoutManager] = None

def get_timeout_manager() -> TimeoutManager:
    """Obtiene instancia singleton del gestor de timeouts"""
    global _timeout_manager
    if _timeout_manager is None:
        _timeout_manager = TimeoutManager()
    return _timeout_manager
