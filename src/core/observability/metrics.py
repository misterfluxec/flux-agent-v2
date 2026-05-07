# =============================================================================
# FLUXAGENT V2 — PROMETHEUS METRICS
# =============================================================================
# Métricas personalizadas para monitoreo de FluxAgent
# Integración con Prometheus y tracking automático
# =============================================================================

import time
import logging
from typing import Dict, Any, Optional, Callable, Union
from functools import wraps
from datetime import datetime
from dataclasses import dataclass

try:
    from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logging.warning("Prometheus client not available. Metrics will be disabled.")

logger = logging.getLogger(__name__)

@dataclass
class MetricConfig:
    """Configuración de métricas"""
    namespace: str = "fluxagent"
    subsystem: Optional[str] = None
    labels: Dict[str, str] = None
    
    def __post_init__(self):
        if self.labels is None:
            self.labels = {}

class PrometheusMetrics:
    """Gestor de métricas Prometheus"""
    
    def __init__(self, config: MetricConfig = None):
        self.config = config or MetricConfig()
        self.registry = CollectorRegistry() if PROMETHEUS_AVAILABLE else None
        
        if PROMETHEUS_AVAILABLE:
            self._init_metrics()
        else:
            self._init_dummy_metrics()
    
    def _init_metrics(self):
        """Inicializa métricas Prometheus reales"""
        
        # Contadores
        self.requests_total = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status_code', 'tenant_id'],
            registry=self.registry
        )
        
        self.request_duration_seconds = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint', 'tenant_id'],
            registry=self.registry
        )
        
        self.cache_operations_total = Counter(
            'cache_operations_total',
            'Total cache operations',
            ['operation', 'namespace', 'tenant_id'],
            registry=self.registry
        )
        
        self.cache_hit_ratio = Gauge(
            'cache_hit_ratio',
            'Cache hit ratio (0-1)',
            ['namespace', 'tenant_id'],
            registry=self.registry
        )
        
        self.database_queries_total = Counter(
            'database_queries_total',
            'Total database queries',
            ['operation', 'table', 'tenant_id'],
            registry=self.registry
        )
        
        self.database_query_duration_seconds = Histogram(
            'database_query_duration_seconds',
            'Database query duration in seconds',
            ['operation', 'table', 'tenant_id'],
            registry=self.registry
        )
        
        self.rate_limit_hits_total = Counter(
            'rate_limit_hits_total',
            'Total rate limit hits',
            ['rule_name', 'tenant_id', 'identifier'],
            registry=self.registry
        )
        
        self.active_connections = Gauge(
            'active_connections',
            'Active connections',
            ['type', 'tenant_id'],
            registry=self.registry
        )
        
        self.business_metrics = Counter(
            'business_events_total',
            'Total business events',
            ['event_type', 'tenant_id', 'agent_id'],
            registry=self.registry
        )
        
        self.error_total = Counter(
            'errors_total',
            'Total errors',
            ['error_type', 'component', 'tenant_id'],
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'queue_size',
            'Queue size',
            ['queue_name', 'tenant_id'],
            registry=self.registry
        )
        
        self.task_duration_seconds = Histogram(
            'task_duration_seconds',
            'Task duration in seconds',
            ['task_type', 'tenant_id'],
            registry=self.registry
        )
        
        # Info metrics
        self.build_info = Info(
            'build_info',
            'Build information',
            ['version', 'environment'],
            registry=self.registry
        )
    
    def _init_dummy_metrics(self):
        """Inicializa métricas dummy cuando Prometheus no está disponible"""
        class DummyMetric:
            def __init__(self, *args, **kwargs):
                pass
            def inc(self, *args, **kwargs):
                pass
            def observe(self, *args, **kwargs):
                pass
            def set(self, *args, **kwargs):
                pass
            def labels(self, *args, **kwargs):
                return self
            def info(self, *args, **kwargs):
                pass
        
        # Crear métricas dummy
        self.requests_total = DummyMetric()
        self.request_duration_seconds = DummyMetric()
        self.cache_operations_total = DummyMetric()
        self.cache_hit_ratio = DummyMetric()
        self.database_queries_total = DummyMetric()
        self.database_query_duration_seconds = DummyMetric()
        self.rate_limit_hits_total = DummyMetric()
        self.active_connections = DummyMetric()
        self.business_metrics = DummyMetric()
        self.error_total = DummyMetric()
        self.queue_size = DummyMetric()
        self.task_duration_seconds = DummyMetric()
        self.build_info = DummyMetric()
    
    def increment_requests_total(
        self,
        method: str,
        endpoint: str,
        status_code: str,
        tenant_id: str = "unknown"
    ):
        """Incrementa contador de requests totales"""
        self.requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            tenant_id=tenant_id
        ).inc()
    
    def observe_request_duration(
        self,
        duration: float,
        method: str,
        endpoint: str,
        tenant_id: str = "unknown"
    ):
        """Registra duración de request"""
        self.request_duration_seconds.labels(
            method=method,
            endpoint=endpoint,
            tenant_id=tenant_id
        ).observe(duration)
    
    def increment_cache_operations(
        self,
        operation: str,  # hit, miss, set, delete
        namespace: str,
        tenant_id: str = "unknown"
    ):
        """Incrementa operaciones de cache"""
        self.cache_operations_total.labels(
            operation=operation,
            namespace=namespace,
            tenant_id=tenant_id
        ).inc()
    
    def set_cache_hit_ratio(
        self,
        ratio: float,
        namespace: str,
        tenant_id: str = "unknown"
    ):
        """Setea ratio de cache hits"""
        self.cache_hit_ratio.labels(
            namespace=namespace,
            tenant_id=tenant_id
        ).set(ratio)
    
    def increment_database_queries(
        self,
        operation: str,  # select, insert, update, delete
        table: str,
        tenant_id: str = "unknown"
    ):
        """Incrementa queries de base de datos"""
        self.database_queries_total.labels(
            operation=operation,
            table=table,
            tenant_id=tenant_id
        ).inc()
    
    def observe_database_query_duration(
        self,
        duration: float,
        operation: str,
        table: str,
        tenant_id: str = "unknown"
    ):
        """Registra duración de query"""
        self.database_query_duration_seconds.labels(
            operation=operation,
            table=table,
            tenant_id=tenant_id
        ).observe(duration)
    
    def increment_rate_limit_hits(
        self,
        rule_name: str,
        tenant_id: str = "unknown",
        identifier: str = "unknown"
    ):
        """Incrementa hits de rate limit"""
        self.rate_limit_hits_total.labels(
            rule_name=rule_name,
            tenant_id=tenant_id,
            identifier=identifier
        ).inc()
    
    def set_active_connections(
        self,
        count: int,
        connection_type: str,  # websocket, database, redis
        tenant_id: str = "unknown"
    ):
        """Setea número de conexiones activas"""
        self.active_connections.labels(
            type=connection_type,
            tenant_id=tenant_id
        ).set(count)
    
    def increment_business_events(
        self,
        event_type: str,  # message_sent, agent_created, conversation_started
        tenant_id: str = "unknown",
        agent_id: str = "unknown"
    ):
        """Incrementa eventos de negocio"""
        self.business_metrics.labels(
            event_type=event_type,
            tenant_id=tenant_id,
            agent_id=agent_id
        ).inc()
    
    def increment_errors(
        self,
        error_type: str,  # validation, database, external_api
        component: str,  # router, service, middleware
        tenant_id: str = "unknown"
    ):
        """Incrementa contador de errores"""
        self.error_total.labels(
            error_type=error_type,
            component=component,
            tenant_id=tenant_id
        ).inc()
    
    def set_queue_size(
        self,
        size: int,
        queue_name: str,
        tenant_id: str = "unknown"
    ):
        """Setea tamaño de cola"""
        self.queue_size.labels(
            queue_name=queue_name,
            tenant_id=tenant_id
        ).set(size)
    
    def observe_task_duration(
        self,
        duration: float,
        task_type: str,  # whatsapp_send, voice_process
        tenant_id: str = "unknown"
    ):
        """Registra duración de tarea"""
        self.task_duration_seconds.labels(
            task_type=task_type,
            tenant_id=tenant_id
        ).observe(duration)
    
    def set_build_info(self, version: str, environment: str):
        """Setea información de build"""
        self.build_info.labels(
            version=version,
            environment=environment
        ).info({
            'build_time': datetime.now().isoformat(),
            'prometheus_enabled': PROMETHEUS_AVAILABLE
        })
    
    def get_metrics(self) -> str:
        """Retorna métricas en formato Prometheus"""
        if PROMETHEUS_AVAILABLE and self.registry:
            return generate_latest(self.registry)
        return "# Prometheus metrics disabled\n"

# Singleton global
_metrics_instance: Optional[PrometheusMetrics] = None

def get_metrics() -> PrometheusMetrics:
    """Obtiene instancia singleton de métricas"""
    global _metrics_instance
    if _metrics_instance is None:
        _metrics_instance = PrometheusMetrics()
    return _metrics_instance

# Decoradores para tracking automático
def track_request_duration(metric_name: str = "http_request"):
    """Decorador para tracking automático de duración de requests"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            metrics = get_metrics()
            start_time = time.time()
            
            try:
                result = await func(*args, **kwargs)
                
                # Extraer información del request
                request = kwargs.get('request')
                if request:
                    method = request.method
                    endpoint = request.url.path
                    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
                    
                    # Incrementar contador de requests exitosos
                    metrics.increment_requests_total(
                        method=method,
                        endpoint=endpoint,
                        status_code="200",
                        tenant_id=tenant_id
                    )
                
                return result
                
            except Exception as e:
                # Extraer información del request
                request = kwargs.get('request')
                if request:
                    method = request.method
                    endpoint = request.url.path
                    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
                    
                    # Incrementar contador de errores
                    metrics.increment_requests_total(
                        method=method,
                        endpoint=endpoint,
                        status_code="500",
                        tenant_id=tenant_id
                    )
                    
                    # Incrementar contador de errores específicos
                    error_type = type(e).__name__.lower()
                    metrics.increment_errors(
                        error_type=error_type,
                        component=func.__module__,
                        tenant_id=tenant_id
                    )
                
                raise
                
            finally:
                # Registrar duración
                duration = time.time() - start_time
                request = kwargs.get('request')
                if request:
                    method = request.method
                    endpoint = request.url.path
                    tenant_id = getattr(request.state, 'tenant_id', 'unknown')
                    
                    metrics.observe_request_duration(
                        duration=duration,
                        method=method,
                        endpoint=endpoint,
                        tenant_id=tenant_id
                    )
        
        return wrapper
    return decorator

def track_cache_performance(namespace: str = "default"):
    """Decorador para tracking automático de performance de cache"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            metrics = get_metrics()
            tenant_id = kwargs.get('tenant_id', 'unknown')
            
            start_time = time.time()
            cache_hit = False
            
            try:
                result = await func(*args, **kwargs)
                
                # Determinar si fue cache hit
                # Esto depende de la implementación específica
                if hasattr(result, '_from_cache'):
                    cache_hit = result._from_cache
                
                operation = "hit" if cache_hit else "miss"
                metrics.increment_cache_operations(
                    operation=operation,
                    namespace=namespace,
                    tenant_id=tenant_id
                )
                
                return result
                
            except Exception as e:
                metrics.increment_cache_operations(
                    operation="error",
                    namespace=namespace,
                    tenant_id=tenant_id
                )
                raise
                
            finally:
                duration = time.time() - start_time
                # Opcional: registrar duración de operaciones de cache
                logger.debug(f"Cache operation duration: {duration:.3f}s")
        
        return wrapper
    return decorator

def track_rate_limit(rule_name: str = "default"):
    """Decorador para tracking automático de rate limiting"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            metrics = get_metrics()
            tenant_id = kwargs.get('tenant_id', 'unknown')
            identifier = kwargs.get('identifier', 'unknown')
            
            try:
                result = await func(*args, **kwargs)
                return result
                
            except Exception as e:
                # Si es error de rate limit, registrar hit
                if "rate_limit" in str(type(e).__name__).lower():
                    metrics.increment_rate_limit_hits(
                        rule_name=rule_name,
                        tenant_id=tenant_id,
                        identifier=identifier
                    )
                
                raise
        
        return wrapper
    return decorator

def track_database_queries(table: str = "unknown"):
    """Decorador para tracking automático de queries de base de datos"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not PROMETHEUS_AVAILABLE:
                return await func(*args, **kwargs)
            
            metrics = get_metrics()
            tenant_id = kwargs.get('tenant_id', 'unknown')
            
            start_time = time.time()
            operation = "unknown"
            
            try:
                result = await func(*args, **kwargs)
                
                # Intentar determinar operación desde el nombre de la función
                func_name = func.__name__.lower()
                if 'select' in func_name or 'get' in func_name:
                    operation = "select"
                elif 'insert' in func_name or 'create' in func_name:
                    operation = "insert"
                elif 'update' in func_name:
                    operation = "update"
                elif 'delete' in func_name or 'remove' in func_name:
                    operation = "delete"
                
                metrics.increment_database_queries(
                    operation=operation,
                    table=table,
                    tenant_id=tenant_id
                )
                
                return result
                
            except Exception as e:
                metrics.increment_database_queries(
                    operation="error",
                    table=table,
                    tenant_id=tenant_id
                )
                raise
                
            finally:
                duration = time.time() - start_time
                metrics.observe_database_query_duration(
                    duration=duration,
                    operation=operation,
                    table=table,
                    tenant_id=tenant_id
                )
        
        return wrapper
    return decorator

# Helper functions para métricas de negocio
def track_business_event(event_type: str, tenant_id: str = "unknown", agent_id: str = "unknown"):
    """Registra evento de negocio"""
    metrics = get_metrics()
    metrics.increment_business_events(
        event_type=event_type,
        tenant_id=tenant_id,
        agent_id=agent_id
    )

def track_error(error_type: str, component: str, tenant_id: str = "unknown"):
    """Registra error"""
    metrics = get_metrics()
    metrics.increment_errors(
        error_type=error_type,
        component=component,
        tenant_id=tenant_id
    )

def track_connection_count(count: int, connection_type: str, tenant_id: str = "unknown"):
    """Registra número de conexiones activas"""
    metrics = get_metrics()
    metrics.set_active_connections(
        count=count,
        connection_type=connection_type,
        tenant_id=tenant_id
    )

def track_queue_size(size: int, queue_name: str, tenant_id: str = "unknown"):
    """Registra tamaño de cola"""
    metrics = get_metrics()
    metrics.set_queue_size(
        size=size,
        queue_name=queue_name,
        tenant_id=tenant_id
    )

def track_task_duration(duration: float, task_type: str, tenant_id: str = "unknown"):
    """Registra duración de tarea"""
    metrics = get_metrics()
    metrics.observe_task_duration(
        duration=duration,
        task_type=task_type,
        tenant_id=tenant_id
    )
