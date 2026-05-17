# =============================================================================
# FLUXAGENT V2 — POLÍTICAS DE PLANES (AGENT CORE)
# =============================================================================

from typing import Protocol
from uuid import UUID
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

class PlanPolicyProtocol(Protocol):
    """Interfaz para la gestión de cuotas y límites por plan."""
    async def can_create_agent(self, tenant_id: UUID) -> bool: ...
    async def get_limit_info(self, tenant_id: UUID) -> dict: ...

class DefaultPlanPolicy:
    """Implementación estándar basada en la tabla tenants."""
    def __init__(self, db: AsyncSession):
        self.db = db

    async def can_create_agent(self, tenant_id: UUID) -> bool:
        result = await self.db.execute(
            text("SELECT max_agents FROM tenants WHERE id = :tid"),
            {"tid": str(tenant_id)}
        )
        plan_row = result.fetchone()
        max_agents = plan_row.max_agents if plan_row else 1
        
        result_count = await self.db.execute(
            text("SELECT COUNT(*) FROM agents WHERE tenant_id = :tid"),
            {"tid": str(tenant_id)}
        )
        current_count = result_count.scalar() or 0
        
        return current_count < max_agents

    async def get_limit_info(self, tenant_id: UUID) -> dict:
        # Implementación para reportar límites a la UI
        return {"current": 0, "max": 0}
