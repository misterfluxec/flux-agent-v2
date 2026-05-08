from fastapi import APIRouter, Depends, HTTPException, Header
from uuid import UUID
from typing import Optional

from src.core.dependencies import get_redis, get_event_bus
from src.services.conversation_engine import ConversationEngine
from src.domain.conversation_state import ConversationState

router = APIRouter(prefix="/api/conversations", tags=["handoff"])

# Nota de seguridad: user_id debería venir del token JWT, pero para 
# facilitar la prueba y el diseño, lo podemos pasar como header o body.
# Lo leeremos de X-User-Id temporalmente o dependeremos de auth.

@router.post("/{conversation_id}/takeover")
async def human_takeover(
    conversation_id: UUID,
    x_user_id: str = Header(..., description="ID del usuario humano que toma control (idealmente desde JWT)"),
    redis=Depends(get_redis),
    event_bus=Depends(get_event_bus)
):
    """
    Permite a un supervisor/humano tomar control de la conversación.
    Bloquea a la IA para que no responda hasta que el humano libere.
    """
    engine = ConversationEngine(redis, event_bus)
    ctx = await engine.get_context(conversation_id)
    
    try:
        async with engine.acquire_lock(conversation_id, x_user_id):
            new_ctx = await engine.transition(
                conv_id=conversation_id,
                new_state=ConversationState.HUMAN_TAKEOVER,
                triggered_by="human",
                tenant_id=ctx.tenant_id,
                agent_id=ctx.agent_id,
                reason="Solicitud manual de supervisor"
            )
            return {
                "status": "success", 
                "state": new_ctx.current_state.value, 
                "message": "Agente en modo observación. Control transferido al humano."
            }
    except PermissionError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{conversation_id}/release")
async def release_to_ai(
    conversation_id: UUID,
    redis=Depends(get_redis),
    event_bus=Depends(get_event_bus)
):
    """
    El humano devuelve el control de la conversación a la IA.
    """
    engine = ConversationEngine(redis, event_bus)
    ctx = await engine.get_context(conversation_id)
    
    if ctx.current_state != ConversationState.HUMAN_TAKEOVER:
        raise HTTPException(
            status_code=400, 
            detail=f"Solo se puede liberar desde takeover humano. Estado actual: {ctx.current_state}"
        )
        
    try:
        new_ctx = await engine.transition(
            conv_id=conversation_id,
            new_state=ConversationState.AI_THINKING,  # Pasa a thinking y luego a idle si no hay más inputs
            triggered_by="human",
            tenant_id=ctx.tenant_id,
            agent_id=ctx.agent_id,
            reason="Humano devuelve control al agente"
        )
        return {"status": "released", "state": new_ctx.current_state.value}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
