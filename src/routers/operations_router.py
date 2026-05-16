from __future__ import annotations
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_usuario_actual, PayloadToken
from database import get_db
from services.operations.hitl_engine import HITLEngine

router = APIRouter(prefix="/api/v1/operations", tags=["Operations"])


class ActionExecutionRequest(BaseModel):
    payload: dict[str, Any]
    ai_audit_log_id: str | None = (
        None  # Enlace a la sugerencia de IA
    )


@router.post("/execute/{action_name}")
async def execute_governed_action(
    action_name: str,
    payload: ActionExecutionRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """
    Ejecuta una acción operacional validada por un humano (HITL).
    Pasa por el Action Governance Layer y registra en el State Journal.
    """
    engine = HITLEngine(
        db=db,
        tenant_id=str(usuario.tenant_id),
        user_id=str(usuario.user_id),
        user_roles=getattr(usuario, "roles", ["ai_operator"]),
        event_bus=request.app.state.event_bus
        if hasattr(request.app.state, "event_bus")
        else None,
    )

    result = await engine.execute_action(
        action_name=action_name.upper(),
        payload=payload.payload,
        ai_audit_log_id=payload.ai_audit_log_id,
    )

    if result.get("status") == "error":
        raise HTTPException(
            status_code=403, detail=result.get("message")
        )

    return result
