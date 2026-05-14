from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Dict, Any
from datetime import datetime
import json

from src.core.database import get_db
# TODO: Import tenant middleware properly once auth is linked
# from src.core.middleware.tenant_isolation import get_tenant_id

router = APIRouter(prefix="/api/v1/governance", tags=["Governance"])

@router.get("/usage/summary")
async def get_usage_summary(
    db: AsyncSession = Depends(get_db), 
    # tenant_id: str = Depends(get_tenant_id)
):
    """
    Returns current usage vs limit for token economy widget.
    """
    # Hardcoded tenant for Beta demo
    tenant_id = "00000000-0000-0000-0000-000000000000" 
    
    # 1. Obtener límites de tenant_quotas
    stmt = text("SELECT max_ai_tokens_per_month, max_workflow_runs_per_month FROM tenant_quotas WHERE tenant_id = :tenant_id")
    result = await db.execute(stmt, {"tenant_id": tenant_id})
    quota = result.fetchone()
    
    limit_tokens = quota.max_ai_tokens_per_month if quota else 1000000
    
    # 2. Obtener consumos reales desde los logs (o Redis, pero logs es más fácil aquí sin inyectar redis_client)
    # Filtrar por el mes actual
    period_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    stmt_usage = text("""
        SELECT resource_type, SUM(consumed_amount) as total
        FROM tenant_usage_logs
        WHERE tenant_id = :tenant_id AND created_at >= :period_start
        GROUP BY resource_type
    """)
    result_usage = await db.execute(stmt_usage, {"tenant_id": tenant_id, "period_start": period_start})
    
    usage = {row.resource_type: int(row.total) for row in result_usage.fetchall()}
    
    consumed_tokens = usage.get('ai_tokens', 0)
    consumed_workflows = usage.get('workflow_runs', 0)
    
    percentage = int((consumed_tokens / limit_tokens) * 100) if limit_tokens > 0 else 0

    return {
        "tokens": {
            "limit": limit_tokens,
            "consumed": consumed_tokens,
            "percentage": percentage
        },
        "workflows": {
            "consumed": consumed_workflows
        }
    }

@router.post("/approval")
async def process_approval(response: Dict[str, Any]):
    """
    Recibe la decisión humana (APPROVED, DENIED) desde el dashboard
    y la inyecta al EventBus para reanudar el Graph Runtime.
    """
    # Mock endpoint para Sprint D.2E
    # TODO: Validar request con ApprovalResponse model
    # TODO: Publicar evento al EventBus para que el Orchestrator reanude el grafo
    request_id = response.get("request_id")
    decision = response.get("decision")
    return {"status": "accepted", "request_id": request_id, "decision": decision, "message": "Approval processed asynchronously"}
