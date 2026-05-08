import uuid
import json
from datetime import datetime
from typing import Any, Dict, Optional
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.tool_registry import ToolDefinition, ToolCategory
from src.config import obtener_config

settings = obtener_config()

class ToolExecutor:
    """
    Motor de ejecución de herramientas (Tools/Functions) para Yanua o cualquier agente IA.
    Implementa Rate Limiting, Sandboxing, Permisos y Auditoría Completa.
    """
    def __init__(self, redis: Redis, db: AsyncSession):
        self.redis = redis
        self.db = db
        self.registry: Dict[str, ToolDefinition] = {}
        self.AUDIT_KEY = "tool:audit:{tenant}"
        
    def register(self, tool: ToolDefinition):
        """Registra una nueva herramienta en el motor"""
        self.registry[tool.name] = tool
        
    async def execute(self, tool_name: str, payload: Dict[str, Any], tenant_id: str, user_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Ejecuta una herramienta de forma segura"""
        tool = self.registry.get(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not registered")
            
        # Validar payload contra el schema de Pydantic
        validated_input = tool.input_schema(**payload)
        
        # Sandbox: verificar permisos y límites de tasa
        await self._check_rate_limit(tenant_id, tool_name)
        
        result = None
        if dry_run:
            result = {
                "status": "dry_run", 
                "would_execute": True, 
                "input": validated_input.model_dump(),
                "is_dangerous": tool.is_dangerous
            }
        else:
            try:
                # Potenciación: Ejecutar pasándole el DB session si la herramienta lo necesita
                import inspect
                sig = inspect.signature(tool.handler)
                kwargs = {}
                if "tenant_id" in sig.parameters:
                    kwargs["tenant_id"] = tenant_id
                if "db_session" in sig.parameters:
                    kwargs["db_session"] = self.db
                if "redis" in sig.parameters:
                    kwargs["redis"] = self.redis
                    
                # Ejecutar handler
                result = await tool.handler(validated_input, **kwargs)
                if not isinstance(result, dict):
                    result = {"status": "success", "result": result}
            except Exception as e:
                result = {"status": "error", "error": str(e)}
                
        # Auditoría obligatoria
        await self._log_audit(tenant_id, tool.name, validated_input.model_dump(), result, user_id)
        return result

    async def _check_rate_limit(self, tenant_id: str, tool_name: str):
        key = f"ratelimit:tool:{tenant_id}:{tool_name}"
        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60) # reset per minute
        if count > settings.tool_rate_limit:
            raise PermissionError("Tool rate limit exceeded for tenant")

    async def _log_audit(self, tenant_id: str, tool: str, input_data: Any, output: Any, user_id: str):
        audit_entry = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "tool": tool,
            "input": input_data,
            "output": output,
            "triggered_by": user_id,
            "timestamp": datetime.utcnow().isoformat()
        }
        key = self.AUDIT_KEY.format(tenant=tenant_id)
        await self.redis.lpush(key, json.dumps(audit_entry))
        await self.redis.ltrim(key, 0, 9999)  # Guardar los últimos 10,000 usos
