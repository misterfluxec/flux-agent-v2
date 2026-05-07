# =============================================================================
# FLUXAGENT V2 — STRUCTURED LOGGING
# =============================================================================
# Logging estructurado en JSON con contexto automático
# Integración con request tracing y métricas
# =============================================================================

import json
import logging
import time
import traceback
from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict
from contextvars import ContextVar

# Context variables para tracing
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)
tenant_id_var: ContextVar[Optional[str]] = ContextVar('tenant_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class LogLevel(Enum):
    """Niveles de log estructurado"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Categorías de logs para mejor organización"""
    HTTP = "http"
    DATABASE = "database"
    CACHE = "cache"
    AUTH = "auth"
    RATE_LIMIT = "rate_limit"
    BUSINESS = "business"
    EXTERNAL_API = "external_api"
    TASK = "task"
    MIDDLEWARE = "middleware"
    ERROR = "error"

@dataclass
class LogContext:
    """Contexto automático para logs"""
    request_id: Optional[str] = None
    tenant_id: Optional[str] = None
    user_id: Optional[str] = None
    method: Optional[str] = None
    path: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    duration_ms: Optional[float] = None
    status_code: Optional[int] = None
    component: Optional[str] = None
    function: Optional[str] = None
    line_number: Optional[int] = None

@dataclass
class StructuredLogEntry:
    """Entrada de log estructurado"""
    timestamp: str
    level: str
    category: str
    message: str
    context: LogContext
    metadata: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    trace: Optional[Dict[str, Any]] = None

class StructuredLogger:
    """Logger estructurado con contexto automático"""
    
    def __init__(self, name: str, level: LogLevel = LogLevel.INFO):
        self.name = name
        self.level = level
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self):
        """Configura logger para salida estructurada"""
        # Remover handlers existentes
        self.logger.handlers.clear()
        
        # Crear handler para JSON
        handler = StructuredLogHandler()
        handler.setLevel(getattr(logging, self.level.value))
        
        # Agregar formatter
        formatter = StructuredLogFormatter()
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        self.logger.setLevel(getattr(logging, self.level.value))
    
    def _create_log_entry(
        self,
        level: LogLevel,
        category: LogCategory,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        **kwargs
    ) -> StructuredLogEntry:
        """Crea entrada de log estructurado"""
        
        # Obtener contexto de las variables de contexto
        context = LogContext(
            request_id=request_id_var.get(),
            tenant_id=tenant_id_var.get(),
            user_id=user_id_var.get(),
            **kwargs
        )
        
        # Agregar información de error si existe
        error_data = None
        if error:
            error_data = {
                "type": type(error).__name__,
                "message": str(error),
                "traceback": traceback.format_exc()
            }
        
        # Agregar información de tracing
        trace_data = None
        if context.request_id:
            trace_data = {
                "request_id": context.request_id,
                "span_id": kwargs.get("span_id"),
                "parent_span_id": kwargs.get("parent_span_id")
            }
        
        return StructuredLogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=level.value,
            category=category.value,
            message=message,
            context=context,
            metadata=metadata,
            error=error_data,
            trace=trace_data
        )
    
    def debug(self, category: LogCategory, message: str, **kwargs):
        """Log a nivel DEBUG"""
        if self.level.value <= LogLevel.DEBUG.value:
            entry = self._create_log_entry(LogLevel.DEBUG, category, message, **kwargs)
            self.logger.debug(json.dumps(asdict(entry), default=str))
    
    def info(self, category: LogCategory, message: str, **kwargs):
        """Log a nivel INFO"""
        if self.level.value <= LogLevel.INFO.value:
            entry = self._create_log_entry(LogLevel.INFO, category, message, **kwargs)
            self.logger.info(json.dumps(asdict(entry), default=str))
    
    def warning(self, category: LogCategory, message: str, **kwargs):
        """Log a nivel WARNING"""
        if self.level.value <= LogLevel.WARNING.value:
            entry = self._create_log_entry(LogLevel.WARNING, category, message, **kwargs)
            self.logger.warning(json.dumps(asdict(entry), default=str))
    
    def error(self, category: LogCategory, message: str, error: Optional[Exception] = None, **kwargs):
        """Log a nivel ERROR"""
        if self.level.value <= LogLevel.ERROR.value:
            entry = self._create_log_entry(LogLevel.ERROR, category, message, error=error, **kwargs)
            self.logger.error(json.dumps(asdict(entry), default=str))
    
    def critical(self, category: LogCategory, message: str, error: Optional[Exception] = None, **kwargs):
        """Log a nivel CRITICAL"""
        if self.level.value <= LogLevel.CRITICAL.value:
            entry = self._create_log_entry(LogLevel.CRITICAL, category, message, error=error, **kwargs)
            self.logger.critical(json.dumps(asdict(entry), default=str))
    
    # Métodos especializados por categoría
    def http_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log de request HTTP"""
        self.info(
            LogCategory.HTTP,
            f"HTTP {method} {path}",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )
    
    def http_error(self, method: str, path: str, status_code: int, error: Exception, **kwargs):
        """Log de error HTTP"""
        self.error(
            LogCategory.HTTP,
            f"HTTP {method} {path} failed",
            method=method,
            path=path,
            status_code=status_code,
            error=error,
            **kwargs
        )
    
    def database_query(self, operation: str, table: str, duration_ms: float, **kwargs):
        """Log de query de base de datos"""
        self.debug(
            LogCategory.DATABASE,
            f"DB {operation} on {table}",
            component="database",
            function=kwargs.get("function"),
            duration_ms=duration_ms,
            metadata={"operation": operation, "table": table},
            **kwargs
        )
    
    def database_error(self, operation: str, table: str, error: Exception, **kwargs):
        """Log de error de base de datos"""
        self.error(
            LogCategory.DATABASE,
            f"DB {operation} failed on {table}",
            component="database",
            error=error,
            metadata={"operation": operation, "table": table},
            **kwargs
        )
    
    def cache_operation(self, operation: str, key: str, hit: bool, **kwargs):
        """Log de operación de cache"""
        self.debug(
            LogCategory.CACHE,
            f"Cache {operation}: {key} ({'HIT' if hit else 'MISS'})",
            component="cache",
            metadata={"operation": operation, "key": key, "hit": hit},
            **kwargs
        )
    
    def cache_error(self, operation: str, key: str, error: Exception, **kwargs):
        """Log de error de cache"""
        self.error(
            LogCategory.CACHE,
            f"Cache {operation} failed: {key}",
            component="cache",
            error=error,
            metadata={"operation": operation, "key": key},
            **kwargs
        )
    
    def auth_event(self, event: str, user_id: str, **kwargs):
        """Log de evento de autenticación"""
        self.info(
            LogCategory.AUTH,
            f"Auth {event}: {user_id}",
            component="auth",
            metadata={"event": event, "user_id": user_id},
            **kwargs
        )
    
    def auth_error(self, event: str, error: Exception, **kwargs):
        """Log de error de autenticación"""
        self.error(
            LogCategory.AUTH,
            f"Auth {event} failed",
            component="auth",
            error=error,
            metadata={"event": event},
            **kwargs
        )
    
    def rate_limit_hit(self, rule_name: str, identifier: str, **kwargs):
        """Log de hit de rate limit"""
        self.warning(
            LogCategory.RATE_LIMIT,
            f"Rate limit hit: {rule_name}",
            component="rate_limit",
            metadata={"rule_name": rule_name, "identifier": identifier},
            **kwargs
        )
    
    def business_event(self, event_type: str, **kwargs):
        """Log de evento de negocio"""
        self.info(
            LogCategory.BUSINESS,
            f"Business event: {event_type}",
            component="business",
            metadata={"event_type": event_type},
            **kwargs
        )
    
    def external_api_call(self, api: str, method: str, url: str, status_code: int, duration_ms: float, **kwargs):
        """Log de llamada a API externa"""
        self.info(
            LogCategory.EXTERNAL_API,
            f"External API {method} {api}",
            component="external_api",
            metadata={"api": api, "method": method, "url": url, "status_code": status_code},
            duration_ms=duration_ms,
            **kwargs
        )
    
    def external_api_error(self, api: str, method: str, url: str, error: Exception, **kwargs):
        """Log de error de API externa"""
        self.error(
            LogCategory.EXTERNAL_API,
            f"External API {method} {api} failed",
            component="external_api",
            error=error,
            metadata={"api": api, "method": method, "url": url},
            **kwargs
        )
    
    def task_event(self, task_type: str, event: str, **kwargs):
        """Log de evento de tarea"""
        self.info(
            LogCategory.TASK,
            f"Task {task_type}: {event}",
            component="task",
            metadata={"task_type": task_type, "event": event},
            **kwargs
        )
    
    def task_error(self, task_type: str, error: Exception, **kwargs):
        """Log de error de tarea"""
        self.error(
            LogCategory.TASK,
            f"Task {task_type} failed",
            component="task",
            error=error,
            metadata={"task_type": task_type},
            **kwargs
        )
    
    def middleware_event(self, middleware: str, event: str, **kwargs):
        """Log de evento de middleware"""
        self.debug(
            LogCategory.MIDDLEWARE,
            f"Middleware {middleware}: {event}",
            component="middleware",
            metadata={"middleware": middleware, "event": event},
            **kwargs
        )

class StructuredLogHandler(logging.Handler):
    """Handler personalizado para logs estructurados"""
    
    def emit(self, record):
        """Emite log estructurado"""
        try:
            # Intentar parsear si ya es JSON estructurado
            if isinstance(record.msg, str) and record.msg.startswith('{'):
                # Ya es JSON estructurado, solo formatear
                log_entry = json.loads(record.msg)
                log_entry['timestamp'] = datetime.fromtimestamp(record.created).isoformat() + "Z"
                log_entry['level'] = record.levelname
                formatted = json.dumps(log_entry, default=str)
            else:
                # Formatear como JSON estructurado
                log_entry = {
                    "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
                    "level": record.levelname,
                    "logger": record.name,
                    "message": record.getMessage(),
                    "module": record.module,
                    "function": record.funcName,
                    "line": record.lineno
                }
                
                # Agregar información de excepción si existe
                if record.exc_info:
                    log_entry["error"] = {
                        "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                        "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                        "traceback": self.format(record) if record.exc_info else None
                    }
                
                formatted = json.dumps(log_entry, default=str)
            
            # Escribir a salida
            self.stream.write(formatted + self.terminator)
            
        except Exception as e:
            # Fallback a logging tradicional
            self.stream.write(f"Error en structured logging: {e}\n")
            self.stream.write(self.format(record) + self.terminator)

class StructuredLogFormatter(logging.Formatter):
    """Formatter para logs estructurados"""
    
    def format(self, record):
        """Formatea registro como JSON"""
        try:
            # Si el mensaje ya es JSON, retornarlo tal cual
            if isinstance(record.msg, str) and record.msg.startswith('{'):
                return record.msg
            
            # Crear entrada estructurada
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat() + "Z",
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno
            }
            
            # Agregar contexto de las variables de contexto
            context = {}
            if request_id := request_id_var.get():
                context["request_id"] = request_id
            if tenant_id := tenant_id_var.get():
                context["tenant_id"] = tenant_id
            if user_id := user_id_var.get():
                context["user_id"] = user_id
            
            if context:
                log_entry["context"] = context
            
            # Agregar información de excepción
            if record.exc_info:
                log_entry["error"] = {
                    "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                    "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                    "traceback": self.formatException(record.exc_info)
                }
            
            return json.dumps(log_entry, default=str)
            
        except Exception:
            # Fallback a formato tradicional
            return self.formatException(record.exc_info) if record.exc_info else super().format(record)

# Funciones helper para contexto
def set_request_context(request_id: str, tenant_id: str = None, user_id: str = None):
    """Establece contexto de request"""
    request_id_var.set(request_id)
    if tenant_id:
        tenant_id_var.set(tenant_id)
    if user_id:
        user_id_var.set(user_id)

def clear_request_context():
    """Limpia contexto de request"""
    request_id_var.set(None)
    tenant_id_var.set(None)
    user_id_var.set(None)

def get_current_context() -> Dict[str, Any]:
    """Obtiene contexto actual"""
    return {
        "request_id": request_id_var.get(),
        "tenant_id": tenant_id_var.get(),
        "user_id": user_id_var.get()
    }

# Factory para loggers estructurados
def get_logger(name: str, level: LogLevel = LogLevel.INFO) -> StructuredLogger:
    """Obtiene logger estructurado"""
    return StructuredLogger(name, level)

# Decorador para logging automático
def log_function_calls(category: LogCategory = LogCategory.BUSINESS, include_args: bool = False):
    """Decorador para logging automático de llamadas a funciones"""
    def decorator(func):
        import functools
        import inspect
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            # Preparar metadata
            metadata = {
                "function": func.__name__,
                "module": func.__module__,
                "line": inspect.getsourcelines(func)[1] if inspect.getsourcelines(func) else None
            }
            
            if include_args:
                # Filtrar argumentos sensibles
                safe_args = {}
                for k, v in kwargs.items():
                    if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                        safe_args[k] = str(v)[:100]  # Limitar longitud
                
                metadata["args"] = safe_args
            
            logger.info(category, f"Function {func.__name__} started", **metadata)
            
            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    category,
                    f"Function {func.__name__} completed",
                    duration_ms=duration_ms,
                    **metadata
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    category,
                    f"Function {func.__name__} failed",
                    error=e,
                    duration_ms=duration_ms,
                    **metadata
                )
                
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            logger = get_logger(func.__module__)
            start_time = time.time()
            
            metadata = {
                "function": func.__name__,
                "module": func.__module__,
                "line": inspect.getsourcelines(func)[1] if inspect.getsourcelines(func) else None
            }
            
            if include_args:
                safe_args = {}
                for k, v in kwargs.items():
                    if not any(sensitive in k.lower() for sensitive in ['password', 'token', 'secret', 'key']):
                        safe_args[k] = str(v)[:100]
                
                metadata["args"] = safe_args
            
            logger.info(category, f"Function {func.__name__} started", **metadata)
            
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                logger.info(
                    category,
                    f"Function {func.__name__} completed",
                    duration_ms=duration_ms,
                    **metadata
                )
                
                return result
                
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.error(
                    category,
                    f"Function {func.__name__} failed",
                    error=e,
                    duration_ms=duration_ms,
                    **metadata
                )
                
                raise
        
        # Determinar si la función es async o síncrona
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
