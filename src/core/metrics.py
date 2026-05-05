"""
Métricas Prometheus para FluxAgent V2
======================================
Expone métricas en http://localhost:8001/metrics
Integrable con Grafana
"""

import logging
import time
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

# Intentar importar prometheus_client (opcional)
try:
    from prometheus_client import Counter, Gauge, Histogram, start_http_server
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("prometheus_client no instalado. Métricas deshabilitadas.")

if PROMETHEUS_AVAILABLE:
    # =============================================================================
    # MÉTRICAS TTS
    # =============================================================================
    TTS_CACHE_HITS = Counter(
        'fluxagent_tts_cache_hits_total',
        'Total de cache hits en TTS',
        ['tenant_id']
    )
    
    TTS_CACHE_MISSES = Counter(
        'fluxagent_tts_cache_misses_total',
        'Total de cache misses en TTS',
        ['tenant_id']
    )
    
    TTS_GENERATION_TIME = Histogram(
        'fluxagent_tts_generation_seconds',
        'Tiempo de generación TTS en segundos',
        ['tenant_id', 'provider'],
        buckets=(0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 30.0, 60.0)
    )
    
    TTS_CIRCUIT_BREAKER_STATE = Gauge(
        'fluxagent_tts_circuit_breaker_state',
        'Estado del circuit breaker: 0=Closed, 1=Open, 2=HalfOpen'
    )
    
    TTS_REQUESTS_TOTAL = Counter(
        'fluxagent_tts_requests_total',
        'Total de requests TTS',
        ['tenant_id', 'status']
    )
    
    # =============================================================================
    # MÉTRICAS CHAT
    # =============================================================================
    CHAT_MESSAGES_RECEIVED = Counter(
        'fluxagent_chat_messages_received_total',
        'Mensajes de chat recibidos',
        ['tenant_id', 'channel']
    )
    
    CHAT_MESSAGES_SENT = Counter(
        'fluxagent_chat_messages_sent_total',
        'Mensajes de chat enviados',
        ['tenant_id', 'channel', 'type']
    )
    
    CHAT_LATENCY = Histogram(
        'fluxagent_chat_processing_seconds',
        'Latencia de procesamiento de chat',
        ['tenant_id'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # =============================================================================
    # MÉTRICAS LLM
    # =============================================================================
    LLM_REQUESTS = Counter(
        'fluxagent_llm_requests_total',
        'Total de requests al LLM',
        ['tenant_id', 'provider', 'model', 'status']
    )
    
    LLM_TOKENS = Counter(
        'fluxagent_llm_tokens_total',
        'Tokens consumidos',
        ['tenant_id', 'type']  # type: input/output
    )
    
    LLM_LATENCY = Histogram(
        'fluxagent_llm_latency_seconds',
        'Latencia de respuestas LLM',
        ['tenant_id', 'model'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
    )
    
    # =============================================================================
    # MÉTRICAS MULTIMEDIA
    # =============================================================================
    STT_REQUESTS = Counter(
        'fluxagent_stt_requests_total',
        'Total de requests STT (Speech to Text)',
        ['tenant_id', 'status']
    )
    
    VISION_REQUESTS = Counter(
        'fluxagent_vision_requests_total',
        'Total de requests de visión',
        ['tenant_id', 'status']
    )
    
    # =============================================================================
    # MÉTRICAS SISTEMA
    # =============================================================================
    ACTIVE_CONNECTIONS = Gauge(
        'fluxagent_active_connections',
        'Conexiones WebSocket activas'
    )
    
    REQUEST_DURATION = Histogram(
        'fluxagent_http_request_duration_seconds',
        'Duración de requests HTTP',
        ['method', 'endpoint', 'status_code'],
        buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5)
    )
    
    # =============================================================================
    # FUNCIONES AUXILIARES
    # =============================================================================
    
    def record_tts_cache_hit(tenant_id: str = "default"):
        """Registrar cache hit."""
        if PROMETHEUS_AVAILABLE:
            TTS_CACHE_HITS.labels(tenant_id=tenant_id).inc()
    
    def record_tts_cache_miss(tenant_id: str = "default"):
        """Registrar cache miss."""
        if PROMETHEUS_AVAILABLE:
            TTS_CACHE_MISSES.labels(tenant_id=tenant_id).inc()
    
    def record_tts_generation_time(tenant_id: str, provider: str, duration: float):
        """Registrar tiempo de generación TTS."""
        if PROMETHEUS_AVAILABLE:
            TTS_GENERATION_TIME.labels(
                tenant_id=tenant_id,
                provider=provider
            ).observe(duration)
    
    def record_circuit_breaker_state(state: int):
        """Registrar estado del circuit breaker (0=CLOSED, 1=OPEN, 2=HALF_OPEN)."""
        if PROMETHEUS_AVAILABLE:
            TTS_CIRCUIT_BREAKER_STATE.set(state)
    
    def record_tts_request(tenant_id: str, status: str):
        """Registrar request TTS."""
        if PROMETHEUS_AVAILABLE:
            TTS_REQUESTS_TOTAL.labels(
                tenant_id=tenant_id,
                status=status
            ).inc()
    
    def record_llm_request(tenant_id: str, provider: str, model: str, status: str):
        """Registrar request LLM."""
        if PROMETHEUS_AVAILABLE:
            LLM_REQUESTS.labels(
                tenant_id=tenant_id,
                provider=provider,
                model=model,
                status=status
            ).inc()
    
    def record_chat_message(tenant_id: str, channel: str, direction: str):
        """Registrar mensaje de chat."""
        if PROMETHEUS_AVAILABLE:
            if direction == "received":
                CHAT_MESSAGES_RECEIVED.labels(
                    tenant_id=tenant_id,
                    channel=channel
                ).inc()
            else:
                CHAT_MESSAGES_SENT.labels(
                    tenant_id=tenant_id,
                    channel=channel,
                    type="text"  # or audio
                ).inc()
    
    def start_metrics_server(port: int = 8001):
        """Iniciar servidor de métricas."""
        if PROMETHEUS_AVAILABLE:
            try:
                start_http_server(port)
                logger.info(f"🚀 Servidor de métricas Prometheus iniciado en puerto {port}")
            except Exception as e:
                logger.error(f"Error iniciando servidor de métricas: {e}")
        else:
            logger.warning("Métricas Prometheus no disponibles")


else:
    # Funciones stub si no hay prometheus
    def record_tts_cache_hit(tenant_id: str = "default"): pass
    def record_tts_cache_miss(tenant_id: str = "default"): pass
    def record_tts_generation_time(tenant_id: str, provider: str, duration: float): pass
    def record_circuit_breaker_state(state: int): pass
    def record_tts_request(tenant_id: str, status: str): pass
    def record_llm_request(tenant_id: str, provider: str, model: str, status: str): pass
    def record_chat_message(tenant_id: str, channel: str, direction: str): pass
    def start_metrics_server(port: int = 8001): pass


# Decorador para medir latencia de funciones async
def track_latency(metric_name: str, **labels):
    """Decorador para trackear latencia de funciones."""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start
                if PROMETHEUS_AVAILABLE and 'chat' in metric_name:
                    # Extraer tenant_id de args si está disponible
                    tenant_id = "default"
                    for arg in args:
                        if hasattr(arg, 'tenant_id'):
                            tenant_id = str(arg.tenant_id)
                    CHAT_LATENCY.labels(tenant_id=tenant_id).observe(duration)
        return wrapper
    return decorator