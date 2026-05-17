import logging
from dramatiq import Middleware
from redis import Redis

logger = logging.getLogger(__name__)

class RetryBudgetMiddleware(Middleware):
    """
    Middleware que implementa un "Presupuesto de Reintentos" (Retry Budgeting).
    Si un porcentaje demasiado alto de mensajes de una cola están fallando (cascading failures),
    detiene temporalmente los reintentos para no ahogar los recursos.
    """
    def __init__(self, redis_client: Redis, max_failures: int = 50, window_secs: int = 60):
        self.redis = redis_client
        self.max_failures = max_failures
        self.window = window_secs

    def after_process_message(self, broker, message, *, result=None, exception=None):
        if exception is not None:
            # Registrar el fallo en Redis
            key = f"dramatiq:budget_failures:{message.queue_name}"
            current = self.redis.incr(key)
            if current == 1:
                self.redis.expire(key, self.window)

    def before_process_message(self, broker, message):
        # Evitar procesar mensajes nuevos o reintentos si estamos en cascading failure
        key = f"dramatiq:budget_failures:{message.queue_name}"
        raw_val = self.redis.get(key)
        
        if raw_val and int(raw_val) > self.max_failures:
            logger.error(f"🚨 RETRY BUDGET EXCEDIDO para la cola {message.queue_name}. Fallos recientes: {int(raw_val)}.")
            # Descartamos temporalmente procesar para permitir recuperación.
            # Lanza RuntimeError para que dramatiq postergue el procesamiento.
            raise RuntimeError(f"Retry Budget Exhausted on {message.queue_name}")
