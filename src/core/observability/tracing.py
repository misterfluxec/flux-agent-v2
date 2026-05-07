# =============================================================================
# FLUXAGENT V2 — OPENTELEMETRY TRACING
# =============================================================================
# Sistema de tracing distribuido con OpenTelemetry
# Integración con Jaeger, Zipkin y otros backends
# =============================================================================

import time
import uuid
import asyncio
import logging
from typing import Dict, Any, Optional, Callable, List
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps

try:
    from opentelemetry import trace, baggage, context
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.zipkin.json import ZipkinExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.semconv.trace import SpanKind
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    logging.warning("OpenTelemetry not available. Tracing will be disabled.")

logger = logging.getLogger(__name__)

class TraceStatus(Enum):
    """Estados de spans"""
    STARTED = "started"
    FINISHED = "finished"
    ERROR = "error"
    TIMEOUT = "timeout"

@dataclass
class SpanContext:
    """Contexto de span para tracing"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: TraceStatus = TraceStatus.STARTED
    tags: Dict[str, Any] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    baggage: Dict[str, Any] = field(default_factory=dict)

class TracingManager:
    """Gestor de tracing con OpenTelemetry"""
    
    def __init__(
        self,
        service_name: str = "fluxagent",
        service_version: str = "1.0.0",
        exporter_type: str = "jaeger",  # jaeger, zipkin, console
        exporter_config: Optional[Dict[str, Any]] = None,
        enabled: bool = True
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.exporter_type = exporter_type
        self.exporter_config = exporter_config or {}
        self.enabled = enabled and OPENTELEMETRY_AVAILABLE
        
        if self.enabled:
            self._setup_tracing()
        else:
            self._setup_mock_tracing()
    
    def _setup_tracing(self):
        """Configura tracing con OpenTelemetry real"""
        try:
            # Configurar exporter
            if self.exporter_type == "jaeger":
                exporter = JaegerExporter(
                    agent_host_name=self.exporter_config.get("host", "localhost"),
                    agent_port=int(self.exporter_config.get("port", 6831)),
                    collector_endpoint=self.exporter_config.get("endpoint"),
                )
            elif self.exporter_type == "zipkin":
                exporter = ZipkinExporter(
                    endpoint=self.exporter_config.get("endpoint", "http://localhost:9411/api/v2/spans"),
                    service_name=self.service_name,
                )
            else:
                # Console exporter para desarrollo
                from opentelemetry.exporter.console import ConsoleSpanExporter
                exporter = ConsoleSpanExporter()
            
            # Configurar tracer provider
            trace.set_tracer_provider(
                TracerProvider(
                    resource={
                        "service.name": self.service_name,
                        "service.version": self.service_version,
                        "telemetry.sdk.name": "opentelemetry",
                        "telemetry.sdk.language": "python",
                        "telemetry.sdk.version": "1.0.0"
                    }
                )
            )
            
            # Configurar span processor
            tracer_provider = trace.get_tracer_provider()
            span_processor = BatchSpanProcessor(exporter)
            tracer_provider.add_span_processor(span_processor)
            
            # Configurar propagación
            set_global_textmap({})
            
            # Configurar instrumentación automática
            self._setup_auto_instrumentation()
            
            # Obtener tracer
            self.tracer = trace.get_tracer(__name__)
            
            logger.info(f"✅ OpenTelemetry tracing configurado: {self.exporter_type}")
            
        except Exception as e:
            logger.error(f"❌ Error configurando OpenTelemetry: {e}")
            self._setup_mock_tracing()
    
    def _setup_mock_tracing(self):
        """Configura mock tracing cuando OpenTelemetry no está disponible"""
        self.tracer = MockTracer()
        logger.warning("⚠️ Usando mock tracing (OpenTelemetry no disponible)")
    
    def _setup_auto_instrumentation(self):
        """Configura instrumentación automática de librerías"""
        try:
            # Instrumentar FastAPI
            FastAPIInstrumentor().instrument()
            
            # Instrumentar SQLAlchemy
            SQLAlchemyInstrumentor().instrument(
                engine=None,  # Se detectará automáticamente
                tracer_provider=trace.get_tracer_provider()
            )
            
            # Instrumentar Redis
            RedisInstrumentor().instrument(
                tracer_provider=trace.get_tracer_provider()
            )
            
            # Instrumentar HTTPX
            HTTPXClientInstrumentor().instrument(
                tracer_provider=trace.get_tracer_provider()
            )
            
            logger.info("✅ Instrumentación automática configurada")
            
        except Exception as e:
            logger.warning(f"⚠️ Error en instrumentación automática: {e}")
    
    def create_span(
        self,
        operation_name: str,
        parent_span: Optional["Span"] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Optional[Dict[str, Any]] = None
    ) -> "Span":
        """Crea un nuevo span"""
        if self.enabled:
            span = self.tracer.start_span(
                operation_name,
                parent=parent_span,
                kind=kind,
                attributes=attributes or {}
            )
            return RealSpan(span, self.tracer)
        else:
            return MockSpan(operation_name, parent_span)
    
    def get_current_span(self) -> Optional["Span"]:
        """Obtiene el span actual"""
        if self.enabled:
            current_span = trace.get_current_span()
            if current_span:
                return RealSpan(current_span, self.tracer)
        return None
    
    def add_baggage(self, key: str, value: str):
        """Agrega baggage al contexto actual"""
        if self.enabled:
            baggage.set_baggage(key, value)
    
    def get_baggage(self, key: str) -> Optional[str]:
        """Obtiene baggage del contexto actual"""
        if self.enabled:
            return baggage.get_baggage(key)
        return None
    
    @contextmanager
    def trace_function(self, operation_name: str, **attributes):
        """Context manager para tracing de funciones"""
        span = self.create_span(operation_name, attributes=attributes)
        try:
            yield span
        except Exception as e:
            span.record_error(e)
            raise
        finally:
            span.finish()
    
    @asynccontextmanager
    async def trace_async_function(self, operation_name: str, **attributes):
        """Context manager para tracing de funciones asíncronas"""
        span = self.create_span(operation_name, attributes=attributes)
        try:
            yield span
        except Exception as e:
            span.record_error(e)
            raise
        finally:
            span.finish()

class Span:
    """Interfaz base para spans"""
    
    def __init__(self, operation_name: str, parent_span: Optional["Span"] = None):
        self.operation_name = operation_name
        self.parent_span = parent_span
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = TraceStatus.STARTED
        self.tags: Dict[str, Any] = {}
        self.logs: List[Dict[str, Any]] = []
    
    def set_tag(self, key: str, value: Any):
        """Agrega tag al span"""
        self.tags[key] = value
    
    def set_tags(self, tags: Dict[str, Any]):
        """Agrega múltiples tags"""
        self.tags.update(tags)
    
    def log_event(self, message: str, level: str = "info", **attributes):
        """Agrega log al span"""
        self.logs.append({
            "timestamp": time.time(),
            "level": level,
            "message": message,
            "attributes": attributes
        })
    
    def record_error(self, error: Exception):
        """Registra error en el span"""
        self.status = TraceStatus.ERROR
        self.log_event(f"Error: {str(error)}", "error", error_type=type(error).__name__)
        self.set_tag("error", True)
        self.set_tag("error.message", str(error))
        self.set_tag("error.type", type(error).__name__)
    
    def finish(self):
        """Finaliza el span"""
        if self.end_time is None:
            self.end_time = time.time()
            if self.status == TraceStatus.STARTED:
                self.status = TraceStatus.FINISHED
    
    def get_duration(self) -> Optional[float]:
        """Obtiene duración del span"""
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    def get_trace_id(self) -> Optional[str]:
        """Obtiene trace ID"""
        return None
    
    def get_span_id(self) -> Optional[str]:
        """Obtiene span ID"""
        return None

class RealSpan(Span):
    """Span real de OpenTelemetry"""
    
    def __init__(self, otel_span, tracer):
        super().__init__(otel_span.name)
        self.otel_span = otel_span
        self.tracer = tracer
    
    def set_tag(self, key: str, value: Any):
        super().set_tag(key, value)
        self.otel_span.set_attribute(key, str(value))
    
    def log_event(self, message: str, level: str = "info", **attributes):
        super().log_event(message, level, **attributes)
        self.otel_span.add_event(
            message,
            attributes={"level": level, **attributes}
        )
    
    def finish(self):
        super().finish()
        if not self.otel_span.end_time:
            self.otel_span.end()
    
    def get_trace_id(self) -> Optional[str]:
        """Obtiene trace ID de OpenTelemetry"""
        from opentelemetry.trace.propagation import get_current_span
        current_span = get_current_span()
        if current_span:
            return format(current_span.get_trace_id(), "032x")
        return None
    
    def get_span_id(self) -> Optional[str]:
        """Obtiene span ID de OpenTelemetry"""
        return format(self.otel_span.get_span_id(), "032x")

class MockSpan(Span):
    """Span mock para cuando OpenTelemetry no está disponible"""
    
    def __init__(self, operation_name: str, parent_span: Optional["Span"] = None):
        super().__init__(operation_name, parent_span)
        self.trace_id = uuid.uuid4().hex
        self.span_id = uuid.uuid4().hex
    
    def get_trace_id(self) -> Optional[str]:
        return self.trace_id
    
    def get_span_id(self) -> Optional[str]:
        return self.span_id

class MockTracer:
    """Tracer mock para desarrollo/testing"""
    
    def start_span(self, operation_name: str, parent=None, kind=None, attributes=None):
        return MockSpan(operation_name, parent)

# Singleton global
_tracing_manager: Optional[TracingManager] = None

def get_tracing_manager() -> TracingManager:
    """Obtiene instancia singleton de tracing"""
    global _tracing_manager
    if _tracing_manager is None:
        _tracing_manager = TracingManager()
    return _tracing_manager

def initialize_tracing(
    service_name: str = "fluxagent",
    service_version: str = "1.0.0",
    exporter_type: str = "jaeger",
    exporter_config: Optional[Dict[str, Any]] = None,
    enabled: bool = True
) -> TracingManager:
    """Inicializa el sistema de tracing"""
    global _tracing_manager
    _tracing_manager = TracingManager(
        service_name=service_name,
        service_version=service_version,
        exporter_type=exporter_type,
        exporter_config=exporter_config,
        enabled=enabled
    )
    return _tracing_manager

# Decoradores para tracing automático
def trace_function(operation_name: Optional[str] = None, include_args: bool = False):
    """Decorador para tracing automático de funciones"""
    def decorator(func: Callable):
        tracing = get_tracing_manager()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            async with tracing.trace_async_function(op_name) as span:
                # Agregar argumentos como tags si se solicita
                if include_args:
                    span.set_tag("function.args_count", len(args))
                    span.set_tag("function.kwargs_count", len(kwargs))
                    
                    # Agregar argumentos no sensibles
                    safe_kwargs = {}
                    for k, v in kwargs.items():
                        if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                            safe_kwargs[k] = str(v)[:100]
                    
                    if safe_kwargs:
                        span.set_tag("function.kwargs", safe_kwargs)
                
                # Agregar metadata de función
                span.set_tag("function.name", func.__name__)
                span.set_tag("function.module", func.__module__)
                span.set_tag("function.is_async", True)
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_tag("function.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("function.success", False)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            with tracing.trace_function(op_name) as span:
                if include_args:
                    span.set_tag("function.args_count", len(args))
                    span.set_tag("function.kwargs_count", len(kwargs))
                    
                    safe_kwargs = {}
                    for k, v in kwargs.items():
                        if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                            safe_kwargs[k] = str(v)[:100]
                    
                    if safe_kwargs:
                        span.set_tag("function.kwargs", safe_kwargs)
                
                span.set_tag("function.name", func.__name__)
                span.set_tag("function.module", func.__module__)
                span.set_tag("function.is_async", False)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("function.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("function.success", False)
                    raise
        
        # Determinar si la función es asíncrona
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def trace_method(operation_name: Optional[str] = None):
    """Decorador para tracing de métodos de clases"""
    def decorator(method: Callable):
        tracing = get_tracing_manager()
        
        @wraps(method)
        async def async_method_wrapper(self, *args, **kwargs):
            op_name = operation_name or f"{self.__class__.__name__}.{method.__name__}"
            
            async with tracing.trace_async_function(op_name) as span:
                span.set_tag("class.name", self.__class__.__name__)
                span.set_tag("method.name", method.__name__)
                span.set_tag("method.is_async", True)
                
                try:
                    result = await method(self, *args, **kwargs)
                    span.set_tag("method.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("method.success", False)
                    raise
        
        @wraps(method)
        def sync_method_wrapper(self, *args, **kwargs):
            op_name = operation_name or f"{self.__class__.__name__}.{method.__name__}"
            
            with tracing.trace_function(op_name) as span:
                span.set_tag("class.name", self.__class__.__name__)
                span.set_tag("method.name", method.__name__)
                span.set_tag("method.is_async", False)
                
                try:
                    result = method(self, *args, **kwargs)
                    span.set_tag("method.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("method.success", False)
                    raise
        
        import inspect
        if inspect.iscoroutinefunction(method):
            return async_method_wrapper
        else:
            return sync_method_wrapper
    
    return decorator

def trace_database_query(table: str, operation: str = "query"):
    """Decorador para tracing de queries de base de datos"""
    def decorator(func: Callable):
        tracing = get_tracing_manager()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = f"database.{operation}.{table}"
            
            async with tracing.trace_async_function(op_name) as span:
                span.set_tag("db.operation", operation)
                span.set_tag("db.table", table)
                span.set_tag("db.system", "postgresql")
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_tag("db.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("db.success", False)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = f"database.{operation}.{table}"
            
            with tracing.trace_function(op_name) as span:
                span.set_tag("db.operation", operation)
                span.set_tag("db.table", table)
                span.set_tag("db.system", "postgresql")
                
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("db.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("db.success", False)
                    raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

def trace_cache_operation(operation: str, namespace: str = "default"):
    """Decorador para tracing de operaciones de cache"""
    def decorator(func: Callable):
        tracing = get_tracing_manager()
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = f"cache.{operation}.{namespace}"
            
            async with tracing.trace_async_function(op_name) as span:
                span.set_tag("cache.operation", operation)
                span.set_tag("cache.namespace", namespace)
                span.set_tag("cache.system", "redis")
                
                try:
                    result = await func(*args, **kwargs)
                    span.set_tag("cache.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("cache.success", False)
                    raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            op_name = f"cache.{operation}.{namespace}"
            
            with tracing.trace_function(op_name) as span:
                span.set_tag("cache.operation", operation)
                span.set_tag("cache.namespace", namespace)
                span.set_tag("cache.system", "redis")
                
                try:
                    result = func(*args, **kwargs)
                    span.set_tag("cache.success", True)
                    return result
                except Exception as e:
                    span.record_error(e)
                    span.set_tag("cache.success", False)
                    raise
        
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
