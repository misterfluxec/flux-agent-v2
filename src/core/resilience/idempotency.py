import hashlib
from redis.asyncio import Redis
from core.tasks.context import task_context

class IdempotencyEngine:
    """
    Controla la idempotencia basada en el TaskContext.
    Soporta explícita (proveniente de un Idempotency-Key) y hash por defecto.
    """
    def __init__(self, redis: Redis, ttl: int = 3600):
        self.redis = redis
        self.ttl = ttl

    async def acquire_key(self, explicit_key: str | None = None) -> bool:
        ctx = task_context.get()
        if not ctx:
            return True # No idempotency without context
            
        key = explicit_key or self._hash_payload(ctx.tenant_id, ctx.task_id)
        redis_key = f"idem:{ctx.tenant_id}:{key}"
        
        # NX=True: Solo se establece si no existe
        # Return True si logramos adquirirlo (no era duplicado)
        return bool(await self.redis.set(redis_key, "1", nx=True, ex=self.ttl))

    @staticmethod
    def _hash_payload(tenant: str, task: str) -> str:
        return hashlib.sha256(f"{tenant}:{task}".encode()).hexdigest()[:16]
