import hashlib
from typing import Optional

class IdempotencyGuardException(Exception):
    pass

class IdempotencyGuard:
    """
    Evita la doble ejecución de herramientas irreversibles guardando su status.
    """
    
    def __init__(self, redis_client):
        self.redis = redis_client
        
    def generate_key(self, tool_id: str, tenant_id: str, customer_id: str, correlation_id: str, parameters_hash: str) -> str:
        """Genera una llave única para el intento de ejecución garantizando aislamiento por tenant y flujo"""
        raw_key = f"{tenant_id}:{customer_id}:{tool_id}:{correlation_id}:{parameters_hash}"
        hashed = hashlib.sha256(raw_key.encode()).hexdigest()
        return f"tool_exec:{hashed}"
        
    async def check_and_lock(self, key: str) -> bool:
        """
        Intenta asegurar el lock para la ejecución. 
        Si el status es PENDING o EXECUTED, devuelve False.
        """
        if not self.redis:
            return True # Si no hay Redis en dev, ignora

        # SETNX (Set if Not eXists) para evitar race conditions
        # Establece a PENDING con un TTL de 1 hora
        is_new = await self.redis.set(key, "PENDING", nx=True, ex=3600)
        return is_new
        
    async def mark_completed(self, key: str, status: str):
        """Marca el hash como EXECUTED o FAILED"""
        if not self.redis:
            return
        
        # En caso de error, dejamos un TTL corto para permitir reintentos posteriores
        ttl = 3600 * 24 * 7 if status == "EXECUTED" else 300 
        await self.redis.set(key, status, ex=ttl)
        
        # Persistencia asíncrona permanente a PostgreSQL para auditoría financiera
        if status in ("EXECUTED", "FAILED"):
            await self.persist_to_audit_log(key, status)
            
    async def persist_to_audit_log(self, key: str, status: str):
        """Mock: Guarda en tabla PostgreSQL (audit_logs) el resultado permanente."""
        # TODO: Implementar guardado real en la BD PostgreSQL
        pass
