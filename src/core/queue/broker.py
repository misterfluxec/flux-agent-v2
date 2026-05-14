# =============================================================================
# FLUXAGENT V2 — DRAMATIQ BROKER CONFIG
# =============================================================================
# Configuración centralizada de cola de tareas con Dramatiq
# Async-native, mejor para FastAPI
# =============================================================================

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from config import obtener_config

config = obtener_config()

# Broker Redis para Dramatiq
redis_broker = RedisBroker(
    url=config.redis_url,
    # Configuración de conexión
    socket_keepalive=True,
    socket_keepalive_options={},
    # Configuración de health checks
    health_check_interval=30
)

# Establecer broker global
dramatiq.set_broker(redis_broker)

# Configuración de colas
QUEUES = {
    "whatsapp": {
        "name": "whatsapp",
        "max_retries": 3,
        "retry_delay": 30,
        "dead_letter": "whatsapp_dlq"
    },
    "voice": {
        "name": "voice", 
        "max_retries": 2,
        "retry_delay": 60,
        "dead_letter": "voice_dlq"
    },
    "analytics": {
        "name": "analytics",
        "max_retries": 1,
        "retry_delay": 300,  # 5 minutos para analytics
        "dead_letter": "analytics_dlq"
    },
    "default": {
        "name": "default",
        "max_retries": 3,
        "retry_delay": 60,
        "dead_letter": "default_dlq"
    }
}

# Configuración de workers
WORKER_CONFIG = {
    "processes": 4,  # Número de procesos worker
    "threads": 2,    # Threads por proceso
    "queues": list(QUEUES.keys()),
    "poll_interval": 1000,  # ms
    "prefetch": 1,  # Mensajes por worker
}

def get_broker():
    """Retorna broker configurado"""
    return redis_broker

def get_queue_config(queue_name: str) -> dict:
    """Retorna configuración de cola específica"""
    return QUEUES.get(queue_name, QUEUES["default"])

def setup_dramatiq():
    """Configura Dramatiq con todas las colas"""
    for queue_config in QUEUES.values():
        dramatiq.declare_queue(
            queue_config["name"],
            max_retries=queue_config["max_retries"],
            retry_delay=queue_config["retry_delay"]
        )
