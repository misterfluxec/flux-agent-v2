import logging
from typing import Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class QuotaExceededError(Exception):
    pass

class TenantGovernanceService:
    """
    Controls usage and billing limits for Tenants.
    Protects the runtime from resource exhaustion using Redis for atomic counters.
    """
    def __init__(self, db: AsyncSession, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    async def check_and_consume(self, tenant_id: str, resource_type: str, amount: int = 1) -> Dict[str, Any]:
        """Verifica cuota y consume si hay disponible. Retorna {allowed: bool, remaining: int, reason: str}"""
        
        # 1. Obtener configuración de cuotas
        stmt = text("SELECT * FROM tenant_quotas WHERE tenant_id = :tenant_id")
        result = await self.db.execute(stmt, {"tenant_id": tenant_id})
        quota = result.fetchone()
        
        if not quota:
            return {"allowed": True, "remaining": -1} # Sin límites configurados

        # Convert RowMapping to dict for easier access if needed, or use column names directly
        # The column names match: max_{resource_type}_per_month
        limit_field = f"max_{resource_type}_per_month"
        limit = getattr(quota, limit_field, None)
        
        if limit is None or limit == -1:
            return {"allowed": True, "remaining": -1}

        # 2. Contador atómico en Redis (clave: quota:{tenant}:{resource}:{YYYY-MM})
        period = datetime.utcnow().strftime("%Y-%m")
        redis_key = f"quota:{tenant_id}:{resource_type}:{period}"
        
        current = await self.redis.get(redis_key)
        current = int(current) if current else 0
        
        if current + amount > limit:
            # Registrar intento de exceso para auditoría
            await self._log_usage(tenant_id, resource_type, 0, metadata={"blocked": True, "limit": limit})
            return {"allowed": False, "remaining": max(0, limit - current), "reason": f"Límite de {resource_type} alcanzado ({limit})"}

        # 3. Consumir en Redis
        new_count = await self.redis.incrby(redis_key, amount)
        await self.redis.expire(redis_key, 35 * 86400) # TTL 35 días
        
        # 4. Registrar en Postgres (asíncrono/background idealmente)
        await self._log_usage(tenant_id, resource_type, amount)
        
        return {"allowed": True, "remaining": limit - new_count}

    async def _log_usage(self, tenant_id: str, resource_type: str, amount: int, metadata: Dict = None):
        stmt = text("""
            INSERT INTO tenant_usage_logs (tenant_id, resource_type, consumed_amount, metadata)
            VALUES (:tenant_id, :resource_type, :amount, :metadata)
        """)
        import json
        await self.db.execute(stmt, {
            "tenant_id": tenant_id, 
            "resource_type": resource_type, 
            "amount": amount, 
            "metadata": json.dumps(metadata or {})
        })
