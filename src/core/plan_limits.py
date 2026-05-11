from fastapi import HTTPException
from functools import wraps
from typing import Callable, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

PLAN_LIMITS = {
    "starter": {
        "max_agents": 1,
        "max_active_quotes": 5,
        "monthly_interactions": 100,  # Límite real de costo (LLM + TTS)
        "allowed_workflows": ["cart_recovery"]
    },
    "growth": {
        "max_agents": 3,
        "max_active_quotes": 50,
        "monthly_interactions": 1000,
        "allowed_workflows": ["cart_recovery", "appointment_reminder_24h", "quote_followup_48h"]
    },
    "enterprise": {
        "max_agents": -1,  # Ilimitado
        "max_active_quotes": -1,
        "monthly_interactions": -1,
        "allowed_workflows": "*"  # Todos
    }
}

async def get_current_agents_count(tenant_id: str, db: AsyncSession) -> int:
    query = text("SELECT COUNT(*) FROM agents WHERE tenant_id = :tenant_id AND status != 'deleted'")
    result = await db.execute(query, {"tenant_id": tenant_id})
    return result.scalar() or 0

def check_plan_limits(plan_key_extractor: Callable[..., str] = lambda kwargs: "starter"):
    """
    Decorador para restringir funcionalidad según el plan del tenant.
    Requiere que kwargs incluya `tenant_id` y `db` si hay que consultar la BD.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Obtener el plan del tenant (en un sistema real podría inyectarse desde el token JWT)
            plan = plan_key_extractor(kwargs)
            limits = PLAN_LIMITS.get(plan, PLAN_LIMITS["starter"])
            
            tenant_id = None
            if "usuario" in kwargs:
                tenant_id = kwargs["usuario"].tenant_id
            elif "tenant_id" in kwargs:
                tenant_id = kwargs["tenant_id"]
                
            db = kwargs.get("db")
            
            # Verificar límite de agentes
            if "create_agent" in func.__name__ and limits["max_agents"] != -1:
                if tenant_id and db:
                    current_count = await get_current_agents_count(tenant_id, db)
                    if current_count >= limits["max_agents"]:
                        logger.warning(f"Tenant {tenant_id} alcanzó el límite de agentes para plan {plan}")
                        raise HTTPException(403, f"Límite de {limits['max_agents']} agentes alcanzado. Mejora tu plan.")
            
            # Verificar workflows
            if "create_workflow" in func.__name__ or "enable_workflow" in func.__name__:
                if limits["allowed_workflows"] != "*":
                    workflow_name = kwargs.get("workflow_name")
                    if workflow_name and workflow_name not in limits["allowed_workflows"]:
                        raise HTTPException(403, f"El workflow '{workflow_name}' requiere el plan Growth o Enterprise.")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
