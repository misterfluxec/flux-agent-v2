"""
ENDPOINTS UNIFICADOS DE WEBHOOKS
================================
API REST para recibir mensajes de cualquier canal.
"""

from fastapi import APIRouter, Request, HTTPException, Header, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
import logging

from channels.router import ChannelRouter
from channels.base import ChannelResponse
from routers.chat_router import procesar_mensaje_entrante
from core.plan_manager import PlanManager
from database import sesion_db
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

router = APIRouter(prefix="/api/v1/channels", tags=["Channels"])

class WebchatMessageRequest(BaseModel):
    message: str
    visitor_id: str
    url: Optional[str] = None


@router.get("/health")
async def channels_health():
    """Verifica el estado de los canales."""
    return {
        "supported_channels": ChannelRouter.list_supported_channels(),
        "status": "ok"
    }


# Rutas de WhatsApp Cloud movidas a src/routers/whatsapp_cloud_router.py

@router.post("/webchat/{tenant_id}")
async def webchat_webhook(
    tenant_id: str,
    payload: WebchatMessageRequest,
    origin: str = Header(None)
):
    """
    Recibe un mensaje desde el Widget Web embebido en el sitio del cliente.
    """
    try:
        from sqlalchemy import text
        from uuid import UUID
        
        async with sesion_db() as db:
            # Check tenant and agent
            res = await db.execute(text("""
                SELECT agent_id 
                FROM canales_config 
                WHERE tenant_id = :tid AND canal = 'webchat' AND estado = 'activo' 
                LIMIT 1
            """), {"tid": tenant_id})
            config_row = res.fetchone()
            
            agent_id = config_row.agent_id if config_row else None

        # Si no hay agente específico, intentamos el router
        if not agent_id:
            try:
                from services.agent_router import resolve_agent_for_channel
                agent_id = await resolve_agent_for_channel(tenant_id, "webchat", payload.message)
            except ValueError:
                # Si no hay router, asignamos al primer agente de ventas del tenant
                async with sesion_db() as db:
                    ag_res = await db.execute(text("SELECT id FROM agents WHERE tenant_id = :tid ORDER BY created_at ASC LIMIT 1"), {"tid": tenant_id})
                    ag_row = ag_res.fetchone()
                    if ag_row:
                        agent_id = ag_row.id
                    else:
                        raise HTTPException(status_code=400, detail="No active agents found for tenant")

        # Call RAG / Ollama synchronous to return immediately to the widget
        respuesta = await procesar_mensaje_entrante(
            tenant_id=UUID(tenant_id),
            agent_id=UUID(str(agent_id)),
            canal="webchat",
            lead_externo_id=payload.visitor_id,
            mensaje_texto=payload.message
        )
        
        # Registrar el uso
        PlanManager.registrar_uso(tenant_id, "messages", 1)
        
        return {
            "status": "success",
            "reply": respuesta
        }

    except Exception as e:
        logger.error(f"Error en webchat webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Error interno del chatbot")


@router.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    bot_token: str
):
    """
    Webhook para Telegram Bot API.
    El bot_token puede pasarse como path param o header.
    """
    try:
        payload = await request.json()
        
        # Verificar que hay un mensaje
        update = payload.get("update", {})
        if "message" not in update and "edited_message" not in update:
            return {"status": "ignored", "reason": "No message"}
        
        # Obtener adapter con el token del bot
        adapter = ChannelRouter.get_adapter("telegram", bot_token=bot_token)
        
        # Procesar mensaje
        message = await adapter.receive_message(payload)
        
        # Mostrar typing
        chat_id = message.metadata.get("chat_id")
        if chat_id:
            await adapter.send_typing_indicator(chat_id, True)
        
        # Buscar configuración del canal telegram
        from sqlalchemy import text
        async with sesion_db() as db:
            res = await db.execute(text("""
                SELECT tenant_id, agent_id 
                FROM canales_config 
                WHERE canal = 'telegram' AND estado = 'activo' 
                LIMIT 1
            """))
            config = res.fetchone()
        
        if not config:
            logger.warning("No hay canal de Telegram configurado")
            return {"status": "error", "reason": "No channel configured"}
        
        # Procesar con el agente
        from uuid import UUID
        respuesta = await procesar_mensaje_entrante(
            tenant_id=UUID(config.tenant_id),
            agent_id=UUID(config.agent_id),
            canal="telegram",
            lead_externo_id=message.sender_id,
            mensaje_texto=message.content if isinstance(message.content, str) else str(message.content)
        )
        
        # Enviar respuesta
        if chat_id:
            await adapter.send_text(chat_id, respuesta)
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Error en Telegram webhook: {e}", exc_info=True)
        return {"status": "error", "reason": str(e)}


@router.get("/supported")
async def list_supported_channels():
    """Lista todos los canales soportados."""
    return {
        "channels": ChannelRouter.list_supported_channels()
    }


@router.post("/test/{channel_name}")
async def test_channel(channel_name: str, request: Request):
    """
    Endpoint de prueba para verificar un canal.
    Envía un mensaje de prueba.
    """
    try:
        body = await request.json()
        recipient = body.get("recipient")
        message = body.get("message", "Test message")
        
        if not recipient:
            raise HTTPException(status_code=400, detail="recipient required")
        
        adapter = ChannelRouter.get_adapter(channel_name)
        
        if not adapter:
            raise HTTPException(
                status_code=404, 
                detail=f"Channel '{channel_name}' not supported"
            )
        
        result = await adapter.send_text(recipient, message)
        
        return {
            "success": result.success,
            "message_id": result.message_id,
            "error": result.error
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error testing channel: {e}")
        raise HTTPException(status_code=500, detail=str(e))