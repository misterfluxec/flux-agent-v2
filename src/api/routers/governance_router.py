from __future__ import annotations
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_usuario_actual, PayloadToken
from database import get_db
from sqlalchemy import text
from uuid import uuid4
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
    from domain.events import EventType, DomainEvent, EventMetadata
    from domain.events import HumanApprovalResponsePayload

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

    tenant_id = str(usuario.tenant_id)
    
    # HITL Validation (Fix for 2.2 Vulnerabilidad de Estado en HITL)
    # Validar que el correlation_id exista en estado 'pending' en la base de datos
    is_uuid = True
    try:
        UUID(correlation_id)
    except ValueError:
        is_uuid = False

    query_str = """
        SELECT id FROM human_tasks 
        WHERE tenant_id = :tenant_id 
          AND status = 'pending'
          AND (context_payload->>'correlation_id' = :corr_id 
               OR (CASE WHEN :is_uuid THEN id::text = :corr_id ELSE false END))
        LIMIT 1
    """
    result = await db.execute(text(query_str), {
        "tenant_id": tenant_id, 
        "corr_id": correlation_id,
        "is_uuid": is_uuid
    })
    
    row = result.fetchone()
    if not row:
        raise HTTPException(
            status_code=400,
            detail=f"No se encontró una solicitud HITL pendiente para el correlation_id: {correlation_id}"
        )
    
    task_id = row[0]

    # Actualizar estado para evitar re-procesamiento
    update_query = text("""
        UPDATE human_tasks
        SET status = :decision,
            updated_at = NOW()
        WHERE id = :task_id
    """)
    await db.execute(update_query, {
        "decision": decision,
        "task_id": task_id
    })
    await db.commit()

    event_bus: EventBus = request.app.state.event_bus

    event = DomainEvent(
        metadata=EventMetadata(
            event_type=EventType.HUMAN_APPROVAL_RESPONSE,
            tenant_id=UUID(tenant_id),
            actor_id=str(usuario.user_id),
            request_origin="api"
        ),
        payload=HumanApprovalResponsePayload(
            correlation_id=correlation_id,
            decision=decision,
            reason=reason,
            reviewed_by=str(usuario.user_id),
        )
    )

    await event_bus.publish(event)
    
    # Telemetría Estructurada para Grafana/Loki
    from core.observability.logging import get_logger, LogCategory
    logger = get_logger("routers.governance")
    logger.business_event(
        "hitl_response_processed",
        correlation_id=correlation_id,
        decision=decision,
        reason=reason,
        tenant_id=tenant_id
    )

    return {
        "status": "published",
        "correlation_id": correlation_id,
        "decision": decision,
    }
