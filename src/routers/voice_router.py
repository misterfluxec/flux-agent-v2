import logging
import base64
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Optional

from core.ws_manager import manager
from core.plan_manager import PlanManager
from core.capabilities.tts import PiperTTSCapability
from services.multimedia import ServicioMultimedia
from routers.chat_router import procesar_mensaje_entrante
from database import sesion_db
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

router = APIRouter(prefix="/api/v1/voice", tags=["Voice Streaming"])


class VoiceStreamManager:
    """Manejador de streaming de voz en tiempo real."""
    
    def __init__(self):
        self.audio_buffers: Dict[str, bytes] = {}
    
    async def handle_voice_websocket(
        self, 
        websocket: WebSocket, 
        tenant_id: str,
        agent_id: str
    ):
        """Maneja la conexión WebSocket para streaming de voz."""
        await websocket.accept()
        logger.info(f"Voice WebSocket conectado: tenant={tenant_id}, agent={agent_id}")
        
        buffer = b""
        
        try:
            await manager.connect(websocket, tenant_id)
            
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                msg_type = message.get("type")
                
                if msg_type == "audio_chunk":
                    audio_b64 = message.get("data", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        buffer += audio_bytes
                        
                elif msg_type == "audio_end":
                    if buffer:
                        await self.process_audio_and_respond(
                            websocket, tenant_id, agent_id, buffer
                        )
                    buffer = b""
                    
                elif msg_type == "text_message":
                    texto = message.get("text", "")
                    if texto:
                        await self.process_text_and_respond(
                            websocket, tenant_id, agent_id, texto
                        )
                        
                elif msg_type == "ping":
                    await websocket.send_json({"type": "pong"})
                    
        except WebSocketDisconnect:
            logger.info(f"Voice WebSocket desconectado: tenant={tenant_id}")
        except Exception as e:
            logger.error(f"Error en Voice WebSocket: {e}")
            try:
                await websocket.send_json({
                    "type": "error", 
                    "message": str(e)
                })
            except:
                pass
        finally:
            manager.disconnect(websocket, tenant_id)
    
    async def process_audio_and_respond(
        self, 
        websocket: WebSocket, 
        tenant_id: str, 
        agent_id: str,
        audio_data: bytes
    ):
        """Procesa audio recibido, transcribe, genera respuesta y responde con voz."""
        try:
            await websocket.send_json({"type": "status", "message": "transcribing"})
            
            audio_b64 = base64.b64encode(audio_data).decode()
            texto = await ServicioMultimedia.transcribir_audio(audio_b64)
            
            if not texto:
                await websocket.send_json({
                    "type": "error", 
                    "message": "No se pudo transcribir el audio"
                })
                return
            
            await websocket.send_json({
                "type": "transcription", 
                "text": texto
            })
            
            respuesta = await procesar_mensaje_entrante(
                tenant_id=tenant_id,
                agent_id=agent_id,
                canal="voice_web",
                lead_externo_id="web_user",
                mensaje_texto=texto
            )
            
            await websocket.send_json({
                "type": "response_text", 
                "text": respuesta
            })
            
            audio_response = await ServicioMultimedia.sintetizar_voz(respuesta)
            if audio_response:
                await websocket.send_json({
                    "type": "audio_response",
                    "audio": audio_response
                })
            else:
                await websocket.send_json({
                    "type": "status",
                    "message": "tts_unavailable"
                })
                
        except Exception as e:
            logger.error(f"Error procesando audio: {e}")
            await websocket.send_json({
                "type": "error",
                "message": f"Error procesando solicitud: {str(e)}"
            })
    
    async def process_text_and_respond(
        self, 
        websocket: WebSocket, 
        tenant_id: str, 
        agent_id: str,
        texto: str
    ):
        """Procesa mensaje de texto y responde."""
        try:
            respuesta = await procesar_mensaje_entrante(
                tenant_id=tenant_id,
                agent_id=agent_id,
                canal="voice_web",
                lead_externo_id="web_user",
                mensaje_texto=texto
            )
            
            await websocket.send_json({
                "type": "response_text",
                "text": respuesta
            })
            
            audio_response = await ServicioMultimedia.sintetizar_voz(respuesta)
            if audio_response:
                await websocket.send_json({
                    "type": "audio_response",
                    "audio": audio_response
                })
                
        except Exception as e:
            logger.error(f"Error procesando texto: {e}")
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })


voice_manager = VoiceStreamManager()


@router.websocket("/stream/{tenant_id}/{agent_id}")
async def voice_stream_endpoint(
    websocket: WebSocket,
    tenant_id: str,
    agent_id: str
):
    """Endpoint WebSocket para streaming de voz."""
    from uuid import UUID
    
    try:
        tenant_uuid = UUID(tenant_id)
        agent_uuid = UUID(agent_id)
    except ValueError:
        await websocket.close(code=4008, reason="Invalid tenant_id or agent_id")
        return
    
    async with sesion_db(tenant_uuid) as db:
        try:
            await PlanManager.check_feature_tenant(tenant_uuid, db, "stt")
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "message": f"Feature no disponible: {str(e)}"
            })
            await websocket.close(code=4003, reason="Feature not allowed")
            return
    
    await voice_manager.handle_voice_websocket(
        websocket, tenant_id, agent_id
    )


@router.websocket("/stream/{tenant_id}")
async def voice_stream_default(
    websocket: WebSocket,
    tenant_id: str
):
    """Endpoint WebSocket para streaming de voz (usa agente por defecto)."""
    from uuid import UUID
    
    try:
        tenant_uuid = UUID(tenant_id)
    except ValueError:
        await websocket.close(code=4008, reason="Invalid tenant_id")
        return
    
    async with sesion_db(tenant_uuid) as db:
        from sqlalchemy import text
        res = await db.execute(text(
            "SELECT id FROM agents WHERE tenant_id = :tid AND estado = 'activa' LIMIT 1"
        ), {"tid": str(tenant_uuid)})
        agent = res.fetchone()
        
        if not agent:
            await websocket.close(code=4004, reason="No active agent")
            return
        
        agent_id = str(agent.id)
    
    await voice_manager.handle_voice_websocket(
        websocket, tenant_id, agent_id
    )