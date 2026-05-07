# =============================================================================
# FLUXAGENT V2 — ASYNC CIRCUIT BREAKER
# =============================================================================
# Implementación avanzada de circuit breaker para dependencias externas
# Protección contra fallos en cascada con recuperación automática
# =============================================================================

import asyncio
import logging
import time
from typing import Callable, Any, Optional, Dict
from functools import wraps
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Estados del circuit breaker"""
    CLOSED = "closed"      # Funcionando normalmente
    OPEN = "open"          # Circuito abierto, rechaza llamadas
    HALF_OPEN = "half_open"  # Probando si el servicio se recuperó

@dataclass
class CircuitBreakerConfig:
    """Configuración del circuit breaker"""
    name: str
    failure_threshold: int = 5          # Fallos antes de abrir
    recovery_timeout: int = 30           # Segundos antes de probar recuperación
    success_threshold: int = 3          # Éxitos para cerrar en half_open
    timeout: float = 30.0               # Timeout por llamada
    expected_exception: type = Exception   # Excepción esperada
    reset_timeout: int = 60             # Timeout máximo para reset manual
    metrics_window: int = 100           # Ventana de métricas
    fallback_enabled: bool = True         # Habilitar fallback
    fallback_response: Any = None        # Respuesta fallback

@dataclass
class CircuitBreakerMetrics:
    """Métricas del circuit breaker"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    timeout_calls: int = 0
    circuit_opens: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    
    @property
    def failure_rate(self) -> float:
        """Tasa de fallos (0-1)"""
        total = self.total_calls
        return self.failed_calls / total if total > 0 else 0.0
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito (0-1)"""
        total = self.total_calls
        return self.successful_calls / total if total > 0 else 0.0

class AsyncCircuitBreaker:
    """Circuit breaker asíncrono avanzado con métricas"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.metrics = CircuitBreakerMetrics()
        self._lock = asyncio.Lock()
        self._last_state_change = datetime.now()
        
        # Callbacks para eventos
        self.on_state_change: Optional[Callable] = None
        self.on_failure: Optional[Callable] = None
        self.on_success: Optional[Callable] = None
        self.on_timeout: Optional[Callable] = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función con protección del circuit breaker"""
        async with self._lock:
            # Verificar estado del circuito
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                    await self._notify_state_change("HALF_OPEN")
                else:
                    # Circuito abierto, lanzar excepción o fallback
                    if self.config.fallback_enabled and self.config.fallback_response is not None:
                        logger.warning(f"Circuit {self.config.name} OPEN - Using fallback")
                        return self.config.fallback_response
                    else:
                        raise CircuitBreakerOpenException(f"Circuit {self.config.name} is OPEN")
            
            # Ejecutar función con timeout
            start_time = time.time()
            try:
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
                
                # Éxito
                duration = time.time() - start_time
                await self._on_success(duration)
                return result
                
            except asyncio.TimeoutError:
                # Timeout
                duration = time.time() - start_time
                await self._on_timeout(duration)
                raise CircuitBreakerTimeoutException(f"Timeout in circuit {self.config.name}")
                
            except self.config.expected_exception as e:
                # Fallo esperado
                duration = time.time() - start_time
                await self._on_failure(e, duration)
                raise
                
            except Exception as e:
                # Fallo inesperado
                duration = time.time() - start_time
                await self._on_failure(e, duration)
                raise
    
    async def _on_success(self, duration: float):
        """Maneja llamada exitosa"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.successful_calls += 1
            self.metrics.last_success_time = datetime.now()
            
            if self.state == CircuitState.HALF_OPEN:
                # Si estamos en half_open y tenemos suficientes éxitos, cerrar
                if (self.metrics.successful_calls % self.config.success_threshold == 0):
                    self.state = CircuitState.CLOSED
                    await self._notify_state_change("CLOSED")
            
            # Notificar callback
            if self.on_success:
                await self._safe_callback(self.on_success, duration)
            
            logger.debug(f"Circuit {self.config.name}: SUCCESS (duration: {duration:.3f}s)")
    
    async def _on_failure(self, exception: Exception, duration: float):
        """Maneja fallo de llamada"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.failed_calls += 1
            self.metrics.last_failure_time = datetime.now()
            
            # Verificar si debemos abrir el circuito
            if self.state == CircuitState.CLOSED:
                if self.metrics.failed_calls >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.metrics.circuit_opens += 1
                    await self._notify_state_change("OPEN")
            
            elif self.state == CircuitState.HALF_OPEN:
                # En half_open, cualquier fallo vuelve a abrir
                self.state = CircuitState.OPEN
                self.metrics.circuit_opens += 1
                await self._notify_state_change("OPEN")
            
            # Notificar callback
            if self.on_failure:
                await self._safe_callback(self.on_failure, exception, duration)
            
            logger.warning(f"Circuit {self.config.name}: FAILURE - {exception}")
    
    async def _on_timeout(self, duration: float):
        """Maneja timeout de llamada"""
        async with self._lock:
            self.metrics.total_calls += 1
            self.metrics.timeout_calls += 1
            self.metrics.last_failure_time = datetime.now()
            
            # Timeout cuenta como fallo
            if self.state == CircuitState.CLOSED:
                if self.metrics.failed_calls >= self.config.failure_threshold:
                    self.state = CircuitState.OPEN
                    self.metrics.circuit_opens += 1
                    await self._notify_state_change("OPEN")
            
            # Notificar callback
            if self.on_timeout:
                await self._safe_callback(self.on_timeout, duration)
            
            logger.warning(f"Circuit {self.config.name}: TIMEOUT (duration: {duration:.3f}s)")
    
    def _should_attempt_reset(self) -> bool:
        """Determina si es hora de intentar resetear"""
        if self.metrics.last_failure_time is None:
            return False
        
        elapsed = datetime.now() - self.metrics.last_failure_time
        return elapsed.total_seconds() >= self.config.recovery_timeout
    
    async def _notify_state_change(self, new_state: str):
        """Notifica cambio de estado"""
        old_state = self.state.value
        self._last_state_change = datetime.now()
        
        logger.info(f"Circuit {self.config.name}: {old_state} → {new_state}")
        
        if self.on_state_change:
            await self._safe_callback(
                self.on_state_change,
                old_state,
                new_state,
                self.metrics
            )
    
    async def _safe_callback(self, callback: Callable, *args, **kwargs):
        """Ejecuta callback de forma segura"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(*args, **kwargs)
            else:
                callback(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in circuit breaker callback: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual y métricas"""
        return {
            "name": self.config.name,
            "state": self.state.value,
            "metrics": {
                "total_calls": self.metrics.total_calls,
                "successful_calls": self.metrics.successful_calls,
                "failed_calls": self.metrics.failed_calls,
                "timeout_calls": self.metrics.timeout_calls,
                "circuit_opens": self.metrics.circuit_opens,
                "failure_rate": self.metrics.failure_rate,
                "success_rate": self.metrics.success_rate,
                "last_failure_time": self.metrics.last_failure_time.isoformat() if self.metrics.last_failure_time else None,
                "last_success_time": self.metrics.last_success_time.isoformat() if self.metrics.last_success_time else None,
                "last_state_change": self._last_state_change.isoformat()
            },
            "config": {
                "failure_threshold": self.config.failure_threshold,
                "recovery_timeout": self.config.recovery_timeout,
                "success_threshold": self.config.success_threshold,
                "timeout": self.config.timeout,
                "fallback_enabled": self.config.fallback_enabled
            }
        }
    
    async def reset(self):
        """Resetea manualmente el circuit breaker a estado cerrado"""
        async with self._lock:
            self.state = CircuitState.CLOSED
            self.metrics = CircuitBreakerMetrics()
            await self._notify_state_change("CLOSED (MANUAL RESET)")
            logger.info(f"Circuit {self.config.name}: MANUAL RESET")

# Diccionario global para instancias
_circuit_breakers: Dict[str, AsyncCircuitBreaker] = {}

def get_circuit_breaker(name: str, config: Optional[CircuitBreakerConfig] = None) -> AsyncCircuitBreaker:
    """Obtiene o crea instancia de circuit breaker"""
    if name not in _circuit_breakers:
        if config is None:
            raise ValueError(f"Circuit breaker '{name}' not found and no config provided")
        _circuit_breakers[name] = AsyncCircuitBreaker(config)
    return _circuit_breakers[name]

def async_circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: int = 30,
    success_threshold: int = 3,
    timeout: float = 30.0,
    expected_exception: type = Exception,
    fallback_enabled: bool = False,
    fallback_response: Any = None
):
    """Decorador para proteger funciones asíncronas con circuit breaker"""
    def decorator(func: Callable):
        config = CircuitBreakerConfig(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            success_threshold=success_threshold,
            timeout=timeout,
            expected_exception=expected_exception,
            fallback_enabled=fallback_enabled,
            fallback_response=fallback_response
        )
        
        breaker = get_circuit_breaker(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        # Agregar metadata para debugging
        wrapper._circuit_breaker_name = name
        wrapper._circuit_breaker_config = config
        
        return wrapper
    
    return decorator

# Excepciones personalizadas
class CircuitBreakerException(Exception):
    """Base exception para circuit breaker"""
    pass

class CircuitBreakerOpenException(CircuitBreakerException):
    """Excepción cuando el circuito está abierto"""
    pass

class CircuitBreakerTimeoutException(CircuitBreakerException):
    """Excepción cuando hay timeout"""
    pass

# Configuraciones predefinidas para servicios comunes
CIRCUIT_BREAKER_CONFIGS = {
    "ollama": CircuitBreakerConfig(
        name="ollama",
        failure_threshold=3,
        recovery_timeout=60,
        timeout=30.0,
        fallback_enabled=True,
        fallback_response={"error": "Ollama service unavailable"}
    ),
    
    "whatsapp_cloud": CircuitBreakerConfig(
        name="whatsapp_cloud",
        failure_threshold=5,
        recovery_timeout=120,
        timeout=15.0,
        fallback_enabled=True,
        fallback_response={"error": "WhatsApp service unavailable"}
    ),
    
    "redis": CircuitBreakerConfig(
        name="redis",
        failure_threshold=3,
        recovery_timeout=30,
        timeout=5.0,
        fallback_enabled=False
    ),
    
    "database": CircuitBreakerConfig(
        name="database",
        failure_threshold=2,
        recovery_timeout=60,
        timeout=10.0,
        fallback_enabled=False
    ),
    
    "external_api": CircuitBreakerConfig(
        name="external_api",
        failure_threshold=5,
        recovery_timeout=300,
        timeout=30.0,
        fallback_enabled=True,
        fallback_response={"error": "External API unavailable"}
    )
}

# Factory para crear circuit breakers con configuración predefinida
def create_circuit_breaker(service_name: str, **overrides) -> AsyncCircuitBreaker:
    """Crea circuit breaker con configuración predefinida y overrides"""
    if service_name not in CIRCUIT_BREAKER_CONFIGS:
        raise ValueError(f"Unknown service: {service_name}")
    
    base_config = CIRCUIT_BREAKER_CONFIGS[service_name]
    
    # Aplicar overrides
    config_dict = {
        "name": base_config.name,
        "failure_threshold": base_config.failure_threshold,
        "recovery_timeout": base_config.recovery_timeout,
        "success_threshold": base_config.success_threshold,
        "timeout": base_config.timeout,
        "expected_exception": base_config.expected_exception,
        "fallback_enabled": base_config.fallback_enabled,
        "fallback_response": base_config.fallback_response,
        **overrides
    }
    
    config = CircuitBreakerConfig(**config_dict)
    return AsyncCircuitBreaker(config)

# Endpoint para monitoreo de circuit breakers
async def get_all_circuit_breakers_status() -> Dict[str, Any]:
    """Retorna estado de todos los circuit breakers"""
    status = {}
    for name, breaker in _circuit_breakers.items():
        status[name] = breaker.get_status()
    return status
