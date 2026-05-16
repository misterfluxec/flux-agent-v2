from __future__ import annotations
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_usuario_actual, PayloadToken
from database import get_db
from services.quota_manager import QuotaManager
from core.exceptions import FluxError

router = APIRouter(
    prefix="/api/v1/governance",
    tags=["Governance"],
)


@router.get("/usage/summary")
async def get_usage_summary(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """
    Resumen de consumo vs límites del plan.
    Usado por el widget de Token Economy en el dashboard.
    """
    redis = request.app.state.redis
    tenant_id = str(usuario.tenant_id)

    manager = QuotaManager(redis=redis, db=db)
    summary = await manager.get_summary(tenant_id)
    return {"tenant_id": tenant_id, **summary}


@router.get("/usage/resources")
async def get_resource_detail(
    resource: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Detalle de consumo de un recurso específico."""
    from domain.usage import UsageResource
    redis = request.app.state.redis
    tenant_id = str(usuario.tenant_id)

    try:
        res_enum = UsageResource(resource)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Recurso '{resource}' no válido.",
        )

    manager = QuotaManager(redis=redis, db=db)
    key = manager._get_period_key(res_enum, tenant_id)
    val = await redis.get(key)
    return {
        "tenant_id": tenant_id,
        "resource": resource,
        "consumed": float(val) if val else 0.0,
    }


@router.post("/approval/respond")
async def respond_to_approval(
    payload: dict[str, Any],
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """
    Respuesta humana a una solicitud de aprobación HITL.
    Publica HumanApprovalResponse al EventBus.
    """
    from core.event_bus import EventBus
    from domain.events import EventType

    correlation_id = payload.get("correlation_id")
    decision = payload.get("decision")
    reason = payload.get("reason", "")

    if not correlation_id or decision not in (
        "approved", "rejected"
    ):
        raise HTTPException(
            status_code=400,
            detail="Faltan correlation_id o decision válida.",
        )

    event_bus: EventBus = request.app.state.event_bus
    tenant_id = str(usuario.tenant_id)

    await event_bus.publish(
        event_type=EventType.HUMAN_APPROVAL_RESPONSE,
        tenant_id=tenant_id,
        payload={
            "correlation_id": correlation_id,
            "decision": decision,
            "reason": reason,
            "reviewed_by": str(usuario.user_id),
        },
    )

    return {
        "status": "published",
        "correlation_id": correlation_id,
        "decision": decision,
    }
