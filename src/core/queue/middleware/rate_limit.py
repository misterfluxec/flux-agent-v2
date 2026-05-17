import logging
import time
from dramatiq import Middleware, RateLimitExceeded
from redis import Redis

logger = logging.getLogger(__name__)

class RateLimitMiddleware(Middleware):
    """
    Middleware de Cuotas / Rate Limiting usando Redis (Sliding Window simple).
    Permite establecer un límite global por actor o por tenant.
    """
    def __init__(self, redis_client: Redis):
        self.redis = redis_client

    def before_process_message(self, broker, message):
        # 1. Chequear si la tarea requiere Rate Limit
        rate_limit = message.options.get("rate_limit")
        if not rate_limit:
            return

        # rate_limit = {"key": "tenant_api", "limit": 100, "window": 60}
        key_suffix = rate_limit.get("key", message.actor_name)
        limit = rate_limit.get("limit", 10)
        window = rate_limit.get("window", 60)
        
        # Opcional: inyectar el tenant_id en la llave si queremos rate-limit por cliente
        ctx = message.options.get("task_context", {})
        tenant_id = ctx.get("tenant_id", "global")
        
        redis_key = f"dramatiq:ratelimit:{tenant_id}:{key_suffix}"
        
        # Implementación simple usando INCR y EXPIRE
        current = self.redis.incr(redis_key)
        if current == 1:
            self.redis.expire(redis_key, window)
            
        if current > limit:
            logger.warning(f"🚫 RateLimit excedido para {redis_key}. Límite {limit}/{window}s.")
            # Al lanzar una excepción que hereda de Exception estándar (o RateLimitExceeded),
            # Dramatiq intentará re-encolar el mensaje con backoff exponencial.
            # Podríamos lanzar dramatiq.RateLimitExceeded, pero eso requiere configuraciones extra.
            raise RuntimeError(f"RateLimitExceeded: {redis_key}")
