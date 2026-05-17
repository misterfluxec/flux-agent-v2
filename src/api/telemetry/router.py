import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

from auth import PayloadToken, get_usuario_actual, get_current_user_ws
from core.events.bus import EventBus
from core.events.types import EventType
from .schema import TaskTelemetryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/telemetry", tags=["Telemetry"])

# Mocks para status en memoria temporal (luego se leerá de DB/Redis real)
# El router interceptará llamadas REST. El status real debe ser persistido por el backend.
# Para esta fase, la base del router está lista para la integración real.

@router.get("/tasks/{task_id}", response_model=TaskTelemetryResponse)
async def get_task_telemetry(
    task_id: str,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """
    Recupera el status actual de una tarea (Polling HTTP fallback).
    En una implementación completa, esto lee de Redis o la DB el status global.
    """
    # TODO: Leer de status almacenado en Redis/DB para el task_id
    # Para efectos del contrato inicial, si no está en caché, devolvemos error.
    raise HTTPException(status_code=404, detail="Estado de tarea no encontrado. Usa WebSockets para actualizaciones en tiempo real.")

@router.websocket("/ws/tasks/{task_id}")
async def task_telemetry_ws(
    websocket: WebSocket,
    task_id: str,
    token: Optional[str] = None
):
    """
    WebSocket endpoint para telemetría en tiempo real de una tarea específica.
    """
    # 1. Autenticación — JWT via query param (?token=<jwt>)
    try:
        usuario = await get_current_user_ws(token)
    except Exception as e:
        logger.warning(f"Intento de conexión WS a telemetría sin token válido: {e}")
        await websocket.close(code=1008, reason="Token inválido")
        return

    await websocket.accept()
    
    # 2. Suscripción al EventBus
    # Obtenemos el bus del state de la app
    app = websocket.app
    if not hasattr(app.state, "event_bus"):
        await websocket.send_json({"error": "EventBus no disponible."})
        await websocket.close()
        return
        
    event_bus: EventBus = app.state.event_bus
    
    # Creamos un handler interno
    async def _on_telemetry_event(event):
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(event.payload.get("event", {}))
        except Exception as e:
            logger.error(f"[WS Telemetry] Error enviando al cliente: {e}")

    # Nos suscribimos específicamente al canal de esta tarea
    # Nota: esto asume que EventBus soporta filtrado por canal o que 
    # podemos usar pubsub directa de Redis
    pubsub = app.state.redis.pubsub()
    channel_name = f"events:tenant:{usuario.tenant_id}:task:{task_id}"
    
    try:
        await pubsub.subscribe(channel_name)
        logger.info(f"Cliente WS suscrito a telemetría de tarea: {task_id}")
        
        while True:
            # Polling sobre la suscripción pubsub del tenant para esta tarea
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message["type"] == "message":
                import json
                data = json.loads(message["data"])
                # Filtrar y emitir el event
                if data.get("type") == EventType.SYSTEM_ALERT.value: # O el type que se use en Broadcaster
                    payload = data.get("payload", {})
                    if payload.get("type") == "telemetry":
                        await websocket.send_json(payload.get("event", {}))
            
            # Ping para mantener vivo el websocket y recibir close desde el cliente
            await asyncio.sleep(0.1)
            
    except WebSocketDisconnect:
        logger.info(f"Cliente WS desconectado de telemetría: {task_id}")
    except Exception as e:
        logger.error(f"Error en WS Telemetry: {e}")
    finally:
        await pubsub.unsubscribe(channel_name)
        await pubsub.close()
