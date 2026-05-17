# =============================================================================
# FLUXAGENT V2 — RESILIENT SERVICES WRAPPER
# =============================================================================
# Wrapper para servicios existentes con Bulkhead Pattern
# Aplica protección contra picos de carga en servicios críticos
# =============================================================================

import logging
from typing import Any, Optional, Dict, List
from functools import wraps

from core.resilience.bulkhead import async_bulkhead, BULKHEAD_CONFIGS
from core.resilience.circuit_breaker import async_circuit_breaker, CIRCUIT_BREAKER_CONFIGS
from core.resilience.retry import async_retry, RETRY_CONFIGS
from core.resilience.timeout import async_timeout, TIMEOUT_CONFIGS

logger = logging.getLogger(__name__)

class ResilientServiceWrapper:
    """Wrapper para añadir resiliencia a servicios existentes"""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self._apply_bulkhead = service_name in ["llm", "whatsapp", "voice", "database"]
        self._apply_circuit_breaker = service_name in ["ollama", "whatsapp_cloud", "redis", "database"]
        self._apply_retry = service_name in ["database", "redis", "http_api", "llm"]
        self._apply_timeout = service_name in ["llm", "whatsapp", "voice", "database"]
    
    def wrap_function(self, func_name: str, func):
        """Envuelve una función con las protecciones de resiliencia apropiadas"""
        
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await self._execute_with_resilience(func_name, func, *args, **kwargs)
        
        return wrapper
    
    async def _execute_with_resilience(self, func_name: str, func, *args, **kwargs):
        """Ejecuta función con las protecciones configuradas"""
        
        # Aplicar timeout primero (capa más externa)
        if self._apply_timeout:
            timeout_config = TIMEOUT_CONFIGS.get(self.service_name)
            if timeout_config:
                func = async_timeout(
                    name=f"{self.service_name}_{func_name}",
                    timeout=timeout_config.timeout,
                    max_timeout=timeout_config.max_timeout,
                    fallback_enabled=timeout_config.fallback_enabled,
                    fallback_response=timeout_config.fallback_response
                )(func)
        
        # Aplicar circuit breaker
        if self._apply_circuit_breaker:
            cb_config = CIRCUIT_BREAKER_CONFIGS.get(self.service_name)
            if cb_config:
                func = async_circuit_breaker(
                    name=f"{self.service_name}_{func_name}",
                    failure_threshold=cb_config.failure_threshold,
                    recovery_timeout=cb_config.recovery_timeout,
                    fallback_enabled=cb_config.fallback_enabled,
                    fallback_response=cb_config.fallback_response
                )(func)
        
        # Aplicar retry
        if self._apply_retry:
            retry_config = RETRY_CONFIGS.get(self.service_name)
            if retry_config:
                func = async_retry(
                    max_attempts=retry_config.max_attempts,
                    base_delay=retry_config.base_delay,
                    backoff_strategy=retry_config.backoff_strategy
                )(func)
        
        # Aplicar bulkhead (último, más interno)
        if self._apply_bulkhead:
            bh_config = BULKHEAD_CONFIGS.get(self.service_name)
            if bh_config:
                func = async_bulkhead(
                    name=f"{self.service_name}_{func_name}",
                    max_concurrent=bh_config.max_concurrent,
                    max_queue=bh_config.max_queue,
                    timeout=bh_config.timeout,
                    reject_when_full=bh_config.reject_when_full,
                    fallback_enabled=bh_config.fallback_enabled,
                    fallback_response=bh_config.fallback_response
                )(func)
        
        return await func(*args, **kwargs)

# Instancias para servicios críticos
_resilient_wrappers: Dict[str, ResilientServiceWrapper] = {}

def get_resilient_wrapper(service_name: str) -> ResilientServiceWrapper:
    """Obtiene wrapper para un servicio específico"""
    if service_name not in _resilient_wrappers:
        _resilient_wrappers[service_name] = ResilientServiceWrapper(service_name)
    return _resilient_wrappers[service_name]

# Decorador para aplicar resiliencia a funciones existentes
def make_resilient(service_name: str, function_name: Optional[str] = None):
    """Decorador para añadir resiliencia a funciones existentes"""
    def decorator(func):
        wrapper = get_resilient_wrapper(service_name)
        func_name_to_use = function_name or func.__name__
        return wrapper.wrap_function(func_name_to_use, func)
    return decorator

# Aplicaciones específicas para servicios existentes
def apply_to_llm_services():
    """Aplica resiliencia a servicios LLM existentes"""
    
    # Aplicar a funciones de Ollama
    from core.llm import call_ollama_async
    
    @make_resilient("llm", "call_ollama")
    async def resilient_call_ollama(prompt: str, model: str, **kwargs):
        return await call_ollama_async(prompt, model, **kwargs)
    
    return resilient_call_ollama

def apply_to_whatsapp_services():
    """Aplica resiliencia a servicios WhatsApp existentes"""
    
    # Aplicar a funciones de WhatsApp
    from services.whatsapp_sender import enviar_whatsapp_async
    
    @make_resilient("whatsapp", "send_message")
    async def resilient_send_whatsapp(phone: str, message: str, **kwargs):
        return await enviar_whatsapp_async(phone, message, **kwargs)
    
    return resilient_send_whatsapp

def apply_to_database_services():
    """Aplica resiliencia a servicios de base de datos"""
    
    # Aplicar a funciones de base de datos
    from database import execute_query_async
    
    @make_resilient("database", "execute_query")
    async def resilient_execute_query(query: str, params: Dict[str, Any], **kwargs):
        return await execute_query_async(query, params, **kwargs)
    
    return resilient_execute_query

def apply_to_voice_services():
    """Aplica resiliencia a servicios de voz"""
    
    # Aplicar a funciones de voz existentes
    from services.voice.pipeline import process_audio_stream
    
    @make_resilient("voice", "process_audio")
    async def resilient_process_audio(audio_bytes: bytes, tenant_id: str, **kwargs):
        return await process_audio_stream(audio_bytes, tenant_id, **kwargs)
    
    return resilient_process_audio

# Endpoint de monitoreo de resiliencia
async def get_resilience_status() -> Dict[str, Any]:
    """Retorna status de todos los componentes de resiliencia"""
    
    from core.resilience.circuit_breaker import get_all_circuit_breakers_status
    from core.resilience.bulkhead import get_all_bulkheads_status
    from core.resilience.retry import get_retry_metrics
    from core.resilience.timeout import get_all_timeouts_status
    
    return {
        "timestamp": "2024-01-01T00:00:00Z",  # TODO: usar timestamp real
        "circuit_breakers": await get_all_circuit_breakers_status(),
        "bulkheads": await get_all_bulkheads_status(),
        "retry_metrics": get_retry_metrics().get_stats(),
        "timeouts": await get_all_timeouts_status(),
        "services_protected": list(_resilient_wrappers.keys())
    }

# Función de inicialización
async def initialize_resilience():
    """Inicializa todos los wrappers de resiliencia"""
    
    logger.info("🛡️ Inicializando resiliencia para servicios críticos")
    
    # Aplicar resiliencia a servicios existentes
    apply_to_llm_services()
    apply_to_whatsapp_services()
    apply_to_database_services()
    apply_to_voice_services()
    
    logger.info(f"✅ Resiliencia aplicada a {len(_resilient_wrappers)} servicios")
    
    # Log de configuración
    for service_name, wrapper in _resilient_wrappers.items():
        config = {
            "bulkhead": wrapper._apply_bulkhead,
            "circuit_breaker": wrapper._apply_circuit_breaker,
            "retry": wrapper._apply_retry,
            "timeout": wrapper._apply_timeout
        }
        logger.info(f"🔧 Servicio {service_name}: {config}")

# Exportar funciones para uso en routers
__all__ = [
    "make_resilient",
    "get_resilient_wrapper",
    "apply_to_llm_services",
    "apply_to_whatsapp_services", 
    "apply_to_database_services",
    "apply_to_voice_services",
    "get_resilience_status",
    "initialize_resilience"
]
