import hashlib
import json
import logging
from dramatiq import Middleware
from dramatiq.middleware import SkipMessage
from redis import Redis

logger = logging.getLogger(__name__)

class IdempotencyMiddleware(Middleware):
    """
    Middleware para evitar procesar la misma tarea múltiples veces.
    Utiliza un hash de los argumentos y del name del actor para
    crear una llave única en Redis con un TTL (ej. 24 horas).
    """

    def __init__(self, redis_client: Redis, ttl_seconds: int = 86400):
        self.redis = redis_client
        self.ttl = ttl_seconds

    def _generate_key(self, message) -> str:
        """Genera un hash único basado en el actor y sus argumentos"""
        # message.queue_name, message.actor_name, message.args, message.kwargs
        raw_data = {
            "actor": message.actor_name,
            "args": message.args,
            "kwargs": message.kwargs
        }
        raw_str = json.dumps(raw_data, sort_keys=True)
        h = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
        return f"dramatiq:idempotency:{h}"

    def before_process_message(self, broker, message):
        # Opcional: solo aplicar a actores que estén marcados explícitamente
        # if not message.options.get("idempotent", False): return

        key = self._generate_key(message)
        
        # nx=True significa "set solo si no existe"
        # Si devuelve True, es la primera vez que vemos esta tarea
        acquired = self.redis.set(key, message.message_id, ex=self.ttl, nx=True)
        
        if not acquired:
            logger.info(f"⏭️ Tarea {message.message_id} ({message.actor_name}) ignorada por IdempotencyMiddleware.")
            # Lanzar SkipMessage hace que Dramatiq aborte el procesamiento sin fallar
            raise SkipMessage("Tarea duplicada detectada")

    def after_process_message(self, broker, message, *, result=None, exception=None):
        # Si la tarea falla, liberamos la llave para permitir un reintento (opcional).
        # Generalmente, Dramatiq tiene su propio RetryMiddleware, así que si queremos
        # que el retry nativo de Dramatiq funcione, podríamos mantener el key o borrarlo.
        # En este diseño, la borraremos SI la tarea falló, para permitir reintentos manuales
        # o el mismo retry de Dramatiq.
        if exception is not None:
            key = self._generate_key(message)
            self.redis.delete(key)
