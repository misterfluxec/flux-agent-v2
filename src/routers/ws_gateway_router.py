import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Optional
from core.realtime_gateway import RealtimeGateway

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])

@router.websocket("/ws/v1/tenant/{tenant_id}")
async def websocket_unified_endpoint(
    websocket: WebSocket, 
    tenant_id: str, 
    user_id: Optional[str] = "default_user",
    last_event_id: Optional[str] = None
):
    """
    Endpoint principal para conexión WebSockets del Frontend de FluxAgent OS.
    Usa el RealtimeGateway para routing inteligente de eventos.
    """
    # Obtener el gateway desde app state (FastAPI lo inyecta en el objeto app,
    # pero desde el websocket lo obtenemos así:)
    gateway: RealtimeGateway = websocket.app.state.realtime_gateway
    
    await gateway.connect(websocket, tenant_id, user_id, last_event_id)
    logger.info(f"🟢 WS Connected: Tenant {tenant_id} | User {user_id}")
    
    try:
        while True:
            # Esperamos comandos de control desde el frontend
            data = await websocket.receive_json()
            command = data.get("command")
            
            if command == "ping":
                await websocket.send_json({"type": "pong"})
                
            elif command == "subscribe":
                event_types = data.get("events", ["*"])
                await gateway.subscribe(tenant_id, user_id, event_types)
                await websocket.send_json({"type": "subscribed", "events": event_types})
                
    except WebSocketDisconnect:
        logger.info(f"🔴 WS Disconnected: Tenant {tenant_id} | User {user_id}")
        await gateway.disconnect(websocket, tenant_id, user_id)
    except Exception as e:
        logger.error(f"⚠️ WS Error: {e}")
        await gateway.disconnect(websocket, tenant_id, user_id)
