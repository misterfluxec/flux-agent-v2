# =============================================================================
# FLUXAGENT V2 — ASYNC BULKHEAD PATTERN
# =============================================================================
# Implementación del patrón Bulkhead para limitar concurrencia
# Previene agotamiento de recursos y protege contra picos de carga
# =============================================================================

import asyncio
import logging
import time
from typing import Callable, Any, Optional, Dict
from functools import wraps
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class BulkheadStrategy(Enum):
    """Estrategias de control de concurrencia"""
    SEMAPHORE = "semaphore"          # Control por semáforo
    THREAD_POOL = "thread_pool"        # Pool de threads
    ASYNC_POOL = "async_pool"          # Pool de tareas asíncronas
    RATE_LIMITED = "rate_limited"      # Rate limiting por tiempo

@dataclass
class BulkheadConfig:
    """Configuración del patrón Bulkhead"""
    name: str
    max_concurrent: int = 10           # Máximo de ejecuciones concurrentes
    max_queue: int = 50                 # Máximo en cola
    timeout: float = 30.0               # Timeout por tarea
    strategy: BulkheadStrategy = BulkheadStrategy.SEMAPHORE
    reject_when_full: bool = True        # Rechazar si está lleno
    metrics_enabled: bool = True         # Habilitar métricas
    fallback_enabled: bool = False       # Habilitar fallback
    fallback_response: Any = None        # Respuesta fallback

@dataclass
class BulkheadMetrics:
    """Métricas del Bulkhead"""
    total_requests: int = 0
    successful_requests: int = 0
    rejected_requests: int = 0
    timeout_requests: int = 0
    queue_full_rejections: int = 0
    current_active: int = 0
    current_queued: int = 0
    peak_concurrent: int = 0
    total_wait_time: float = 0.0
    avg_wait_time: float = 0.0
    
    @property
    def success_rate(self) -> float:
        """Tasa de éxito (0-1)"""
        total = self.total_requests
        return self.successful_requests / total if total > 0 else 0.0
    
    @property
    def rejection_rate(self) -> float:
        """Tasa de rechazo (0-1)"""
        total = self.total_requests
        return self.rejected_requests / total if total > 0 else 0.0

class AsyncBulkhead:
    """Implementación del patrón Bulkhead asíncrono"""
    
    def __init__(self, config: BulkheadConfig):
        self.config = config
        self.metrics = BulkheadMetrics()
        self._semaphore = None
        self._queue = None
        self._executor = None
        self._setup_bulkhead()
    
    def _setup_bulkhead(self):
        """Configura el bulkhead según la estrategia"""
        if self.config.strategy == BulkheadStrategy.SEMAPHORE:
            self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
            self._queue = asyncio.Queue(maxsize=self.config.max_queue)
            
        elif self.config.strategy == BulkheadStrategy.ASYNC_POOL:
            self._executor = asyncio.ThreadPoolExecutor(
                max_workers=self.config.max_concurrent
            )
            self._queue = asyncio.Queue(maxsize=self.config.max_queue)
            
        elif self.config.strategy == BulkheadStrategy.THREAD_POOL:
            import concurrent.futures
            self._executor = concurrent.futures.ThreadPoolExecutor(
                max_workers=self.config.max_concurrent
            )
            self._queue = asyncio.Queue(maxsize=self.config.max_queue)
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función con protección del bulkhead"""
        start_time = time.time()
        
        try:
            # Incrementar métricas
            self.metrics.total_requests += 1
            
            # Verificar si hay espacio en la cola
            if (self.config.reject_when_full and 
                self._queue and 
                self._queue.full()):
                
                self.metrics.rejected_requests += 1
                self.metrics.queue_full_rejections += 1
                
                if self.config.fallback_enabled:
                    logger.warning(f"Bulkhead {self.config.name}: Queue full, using fallback")
                    return self.config.fallback_response
                else:
                    raise BulkheadFullException(f"Bulkhead {self.config.name} is full")
            
            # Esperar turno
            wait_start = time.time()
            await self._wait_for_turn()
            wait_time = time.time() - wait_start
            
            # Actualizar métricas de espera
            self.metrics.total_wait_time += wait_time
            self.metrics.avg_wait_time = (
                self.metrics.total_wait_time / self.metrics.total_requests
            )
            
            # Ejecutar con timeout
            try:
                self.metrics.current_active += 1
                self.metrics.peak_concurrent = max(
                    self.metrics.peak_concurrent,
                    self.metrics.current_active
                )
                
                result = await asyncio.wait_for(
                    self._execute_func(func, *args, **kwargs),
                    timeout=self.config.timeout
                )
                
                self.metrics.successful_requests += 1
                return result
                
            except asyncio.TimeoutError:
                self.metrics.timeout_requests += 1
                raise BulkheadTimeoutException(f"Timeout in bulkhead {self.config.name}")
                
            finally:
                self.metrics.current_active -= 1
                
        except Exception as e:
            if not isinstance(e, (BulkheadFullException, BulkheadTimeoutException)):
                # Error inesperado
                logger.error(f"Error in bulkhead {self.config.name}: {e}")
                raise
            raise
    
    async def _wait_for_turn(self):
        """Espera turno según la estrategia"""
        if self.config.strategy == BulkheadStrategy.SEMAPHORE:
            await self._semaphore.acquire()
            
        elif self._queue:
            await self._queue.put(None)  # Señal de turno
    
    async def _execute_func(self, func: Callable, *args, **kwargs) -> Any:
        """Ejecuta función según la estrategia"""
        try:
            if self.config.strategy == BulkheadStrategy.SEMAPHORE:
                result = await func(*args, **kwargs)
                self._semaphore.release()
                return result
                
            elif self.config.strategy in [BulkheadStrategy.ASYNC_POOL, BulkheadStrategy.THREAD_POOL]:
                loop = asyncio.get_event_loop()
                if self._queue:
                    await self._queue.get()
                
                if asyncio.iscoroutinefunction(func):
                    result = await func(*args, **kwargs)
                else:
                    result = await loop.run_in_executor(
                        self._executor, func, *args, **kwargs
                    )
                
                return result
                
        finally:
            if self._queue and not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual y métricas"""
        return {
            "name": self.config.name,
            "strategy": self.config.strategy.value,
            "metrics": {
                "total_requests": self.metrics.total_requests,
                "successful_requests": self.metrics.successful_requests,
                "rejected_requests": self.metrics.rejected_requests,
                "timeout_requests": self.metrics.timeout_requests,
                "queue_full_rejections": self.metrics.queue_full_rejections,
                "current_active": self.metrics.current_active,
                "current_queued": self._queue.qsize() if self._queue else 0,
                "peak_concurrent": self.metrics.peak_concurrent,
                "success_rate": self.metrics.success_rate,
                "rejection_rate": self.metrics.rejection_rate,
                "avg_wait_time": self.metrics.avg_wait_time
            },
            "config": {
                "max_concurrent": self.config.max_concurrent,
                "max_queue": self.config.max_queue,
                "timeout": self.config.timeout,
                "reject_when_full": self.config.reject_when_full,
                "fallback_enabled": self.config.fallback_enabled
            }
        }
    
    async def shutdown(self):
        """Cierra recursos del bulkhead"""
        if self._executor:
            self._executor.shutdown(wait=True)
        
        logger.info(f"Bulkhead {self.config.name} shutdown completed")

# Diccionario global para instancias
_bulkheads: Dict[str, AsyncBulkhead] = {}

def get_bulkhead(name: str, config: Optional[BulkheadConfig] = None) -> AsyncBulkhead:
    """Obtiene o crea instancia de bulkhead"""
    if name not in _bulkheads:
        if config is None:
            raise ValueError(f"Bulkhead '{name}' not found and no config provided")
        _bulkheads[name] = AsyncBulkhead(config)
    return _bulkheads[name]

def async_bulkhead(
    name: str,
    max_concurrent: int = 10,
    max_queue: int = 50,
    timeout: float = 30.0,
    strategy: BulkheadStrategy = BulkheadStrategy.SEMAPHORE,
    reject_when_full: bool = True,
    fallback_enabled: bool = False,
    fallback_response: Any = None
):
    """Decorador para proteger funciones con patrón Bulkhead"""
    def decorator(func: Callable):
        config = BulkheadConfig(
            name=name,
            max_concurrent=max_concurrent,
            max_queue=max_queue,
            timeout=timeout,
            strategy=strategy,
            reject_when_full=reject_when_full,
            fallback_enabled=fallback_enabled,
            fallback_response=fallback_response
        )
        
        bulkhead = get_bulkhead(name, config)
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await bulkhead.execute(func, *args, **kwargs)
        
        # Agregar metadata para debugging
        wrapper._bulkhead_name = name
        wrapper._bulkhead_config = config
        
        return wrapper
    
    return decorator

# Configuraciones predefinidas para servicios comunes
BULKHEAD_CONFIGS = {
    "database_queries": BulkheadConfig(
        name="database_queries",
        max_concurrent=20,
        max_queue=100,
        timeout=10.0,
        strategy=BulkheadStrategy.SEMAPHORE,
        reject_when_full=True
    ),
    
    "http_requests": BulkheadConfig(
        name="http_requests",
        max_concurrent=50,
        max_queue=200,
        timeout=30.0,
        strategy=BulkheadStrategy.ASYNC_POOL,
        reject_when_full=True
    ),
    
    "llm_requests": BulkheadConfig(
        name="llm_requests",
        max_concurrent=5,
        max_queue=50,
        timeout=60.0,
        strategy=BulkheadStrategy.SEMAPHORE,
        reject_when_full=True,
        fallback_enabled=True,
        fallback_response={"error": "LLM service overloaded"}
    ),
    
    "voice_processing": BulkheadConfig(
        name="voice_processing",
        max_concurrent=3,
        max_queue=20,
        timeout=120.0,
        strategy=BulkheadStrategy.THREAD_POOL,
        reject_when_full=True,
        fallback_enabled=True,
        fallback_response={"error": "Voice service busy"}
    ),
    
    "file_uploads": BulkheadConfig(
        name="file_uploads",
        max_concurrent=5,
        max_queue=30,
        timeout=300.0,
        strategy=BulkheadStrategy.SEMAPHORE,
        reject_when_full=True,
        fallback_enabled=True,
        fallback_response={"error": "Upload service busy"}
    ),
    
    "whatsapp_sends": BulkheadConfig(
        name="whatsapp_sends",
        max_concurrent=10,
        max_queue=100,
        timeout=30.0,
        strategy=BulkheadStrategy.SEMAPHORE,
        reject_when_full=True,
        fallback_enabled=True,
        fallback_response={"error": "WhatsApp service busy"}
    )
}

def create_bulkhead(service_name: str, **overrides) -> AsyncBulkhead:
    """Crea bulkhead con configuración predefinida y overrides"""
    if service_name not in BULKHEAD_CONFIGS:
        raise ValueError(f"Unknown service: {service_name}")
    
    base_config = BULKHEAD_CONFIGS[service_name]
    
    # Aplicar overrides
    config_dict = {
        "name": base_config.name,
        "max_concurrent": base_config.max_concurrent,
        "max_queue": base_config.max_queue,
        "timeout": base_config.timeout,
        "strategy": base_config.strategy,
        "reject_when_full": base_config.reject_when_full,
        "fallback_enabled": base_config.fallback_enabled,
        "fallback_response": base_config.fallback_response,
        **overrides
    }
    
    config = BulkheadConfig(**config_dict)
    return AsyncBulkhead(config)

# Endpoint para monitoreo de bulkheads
async def get_all_bulkheads_status() -> Dict[str, Any]:
    """Retorna estado de todos los bulkheads"""
    status = {}
    for name, bulkhead in _bulkheads.items():
        status[name] = bulkhead.get_status()
    return status

# Excepciones personalizadas
class BulkheadException(Exception):
    """Base exception para bulkhead"""
    pass

class BulkheadFullException(BulkheadException):
    """Excepción cuando el bulkhead está lleno"""
    pass

class BulkheadTimeoutException(BulkheadException):
    """Excepción cuando hay timeout en el bulkhead"""
    pass

# Utilidades para gestión de bulkheads
class BulkheadManager:
    """Gestor para administración de bulkheads"""
    
    def __init__(self):
        self.bulkheads = _bulkheads
    
    def add_bulkhead(self, bulkhead: AsyncBulkhead):
        """Agrega un bulkhead al gestor"""
        self.bulkheads[bulkhead.config.name] = bulkhead
        logger.info(f"Bulkhead added: {bulkhead.config.name}")
    
    def remove_bulkhead(self, name: str) -> bool:
        """Remueve un bulkhead del gestor"""
        if name in self.bulkheads:
            bulkhead = self.bulkheads.pop(name)
            asyncio.create_task(bulkhead.shutdown())
            logger.info(f"Bulkhead removed: {name}")
            return True
        return False
    
    def get_bulkhead(self, name: str) -> Optional[AsyncBulkhead]:
        """Obtiene un bulkhead por nombre"""
        return self.bulkheads.get(name)
    
    def list_bulkheads(self) -> list[str]:
        """Lista todos los bulkheads"""
        return list(self.bulkheads.keys())
    
    async def shutdown_all(self):
        """Cierra todos los bulkheads"""
        for bulkhead in self.bulkheads.values():
            await bulkhead.shutdown()
        self.bulkheads.clear()
        logger.info("All bulkheads shutdown completed")
    
    def get_global_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas globales de todos los bulkheads"""
        global_metrics = {
            "total_bulkheads": len(self.bulkheads),
            "total_requests": 0,
            "successful_requests": 0,
            "rejected_requests": 0,
            "timeout_requests": 0,
            "current_active": 0,
            "peak_concurrent": 0
        }
        
        for bulkhead in self.bulkheads.values():
            metrics = bulkhead.metrics
            global_metrics["total_requests"] += metrics.total_requests
            global_metrics["successful_requests"] += metrics.successful_requests
            global_metrics["rejected_requests"] += metrics.rejected_requests
            global_metrics["timeout_requests"] += metrics.timeout_requests
            global_metrics["current_active"] += metrics.current_active
            global_metrics["peak_concurrent"] = max(
                global_metrics["peak_concurrent"],
                metrics.peak_concurrent
            )
        
        # Calcular tasas globales
        total = global_metrics["total_requests"]
        if total > 0:
            global_metrics["success_rate"] = global_metrics["successful_requests"] / total
            global_metrics["rejection_rate"] = global_metrics["rejected_requests"] / total
        else:
            global_metrics["success_rate"] = 0.0
            global_metrics["rejection_rate"] = 0.0
        
        return global_metrics

# Singleton global para el gestor
_bulkhead_manager: Optional[BulkheadManager] = None

def get_bulkhead_manager() -> BulkheadManager:
    """Obtiene instancia singleton del gestor de bulkheads"""
    global _bulkhead_manager
    if _bulkhead_manager is None:
        _bulkhead_manager = BulkheadManager()
    return _bulkhead_manager
