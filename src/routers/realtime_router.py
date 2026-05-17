from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import asyncio
import json

router = APIRouter(prefix="/ws/v1", tags=["realtime"])

class ConnectionManager:
    """
    WebSocket Gateway Manager (Sprint 4A.1).
    Soporta aislamiento por tenant, particionamiento de channels, y heartbeats.
    """
    def __init__(self):
        # channel_name -> conjunto de WebSockets
        # ej: "tenant:1234:operations" -> {ws1, ws2}
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, tenant_id: str, channel: str):
        await websocket.accept()
        channel_id = f"tenant:{tenant_id}:{channel}"
        
        if channel_id not in self.active_connections:
            self.active_connections[channel_id] = set()
            
        self.active_connections[channel_id].add(websocket)
        # Enviar acknowledge inicial
        await websocket.send_json({"event": "connected", "channel": channel_id})

    def disconnect(self, websocket: WebSocket, tenant_id: str, channel: str):
        channel_id = f"tenant:{tenant_id}:{channel}"
        if channel_id in self.active_connections:
            self.active_connections[channel_id].discard(websocket)
            if not self.active_connections[channel_id]:
                del self.active_connections[channel_id]

    async def broadcast_to_channel(self, tenant_id: str, channel: str, message: dict, priority: str = "NORMAL"):
        """
        Emite un mensaje a todos los clientes suscritos al canal del tenant.
        Respeta la priority (en una implementación completa asincrónica usaría colas distintas).
        """
        channel_id = f"tenant:{tenant_id}:{channel}"
        if channel_id in self.active_connections:
            # Backpressure Protection simplificada:
            # Si el cliente está muy lento, asyncio.wait con timeout evitaría bloquear el broadcast
            tasks = [ws.send_json(message) for ws in self.active_connections[channel_id]]
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

manager = ConnectionManager()

@router.websocket("/{tenant_id}/{channel}")
async def websocket_endpoint(websocket: WebSocket, tenant_id: str, channel: str):
    """
    Endpoint de WebSocket. Los channels permitidos son:
    - operations
    - payments
    - inventory
    - connectors
    - alerts
    """
    allowed_channels = ["operations", "payments", "inventory", "connectors", "alerts"]
    if channel not in allowed_channels:
        await websocket.close(code=4003, reason="Invalid channel")
        return

    await manager.connect(websocket, tenant_id, channel)
    try:
        while True:
            # Implementación de Heartbeat/Ping
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id, channel)
    except Exception as e:
        manager.disconnect(websocket, tenant_id, channel)
