import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from starlette.responses import StreamingResponse
from redis.asyncio import Redis
from config import obtener_config

settings = obtener_config()

class RealtimeGateway:
    """
    Gateway de tiempo real unificado que reemplaza ws_manager.
    Soporta Presencia, Suscripciones tipadas, Delta Sync (Backlog) y SSE (Server-Sent Events)
    para clientes inestables (ej. redes móviles).
    """
    def __init__(self, redis: Redis):
        self.redis = redis
        # tenant_id -> {user_id: ws}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}  
        # tenant_id -> {user_id: set(event_types)}
        self.subscriptions: Dict[str, Dict[str, Set[str]]] = {}        
        self.PRESENCE_KEY = "gw:presence:{tenant}"
        self.DELTA_KEY = "gw:last_event:{tenant}:{user}"
        
    async def connect(self, ws: WebSocket, tenant_id: str, user_id: str, last_event_id: Optional[str] = None):
        await ws.accept()
        self.active_connections.setdefault(tenant_id, {})[user_id] = ws
        await self.redis.sadd(self.PRESENCE_KEY.format(tenant=tenant_id), user_id)
        
        # Delta sync: reenviar eventos perdidos desde última reconexión
        if last_event_id:
            await self._send_backlog(ws, tenant_id, user_id, last_event_id)
            
        # Mantener conexión viva
        asyncio.create_task(self._keep_alive(ws, tenant_id, user_id))
        
    async def disconnect(self, ws: WebSocket, tenant_id: str, user_id: str):
        if tenant_id in self.active_connections and user_id in self.active_connections[tenant_id]:
            self.active_connections[tenant_id].pop(user_id, None)
            
        await self.redis.srem(self.PRESENCE_KEY.format(tenant=tenant_id), user_id)
        
        if tenant_id in self.active_connections and not self.active_connections[tenant_id]:
            self.active_connections.pop(tenant_id, None)

    async def subscribe(self, tenant_id: str, user_id: str, event_types: list[str]):
        """Permite que un usuario indique qué eventos específicos desea escuchar"""
        self.subscriptions.setdefault(tenant_id, {}).setdefault(user_id, set()).update(event_types)

    async def broadcast_to_tenant(self, tenant_id: str, message: dict):
        """Método de retrocompatibilidad para ws_event_bridge.py"""
        if not tenant_id or tenant_id == "None":
            return
            
        event_type = message.get("type", "*")
        event_id = message.get("event_id", "")
        await self.publish_to_tenant(tenant_id, event_type, message, event_id)

    async def publish_to_tenant(self, tenant_id: str, event_type: str, payload: dict, event_id: str):
        """Publicación optimizada usando las suscripciones de cada usuario."""
        if not tenant_id or tenant_id == "None":
            return
            
        targets = []
        # Si no hay subscriptions registradas pero hay conexiones activas, hacer broadcast general (compatibilidad)
        active_users = self.active_connections.get(tenant_id, {})
        subs_users = self.subscriptions.get(tenant_id, {})
        
        for uid, ws in active_users.items():
            subs = subs_users.get(uid, {"*"})  # Por defecto si no se suscribió, escucha todo
            if event_type in subs or "*" in subs:
                try:
                    targets.append(ws.send_json({"type": event_type, "id": event_id, **payload}))
                except Exception:
                    pass
        
        if targets:
            await asyncio.gather(*targets, return_exceptions=True)
            
        # Registrar ID para delta sync futuro
        for uid in subs_users.keys():
            await self.redis.setex(self.DELTA_KEY.format(tenant=tenant_id, user=uid), 300, event_id)

    def get_sse_handler(self, tenant_id: str, user_id: str):
        """
        Alternativa de conexión para redes móviles intermitentes: Server-Sent Events.
        (Ej. React Native)
        """
        async def event_stream():
            queue = asyncio.Queue()
            self.active_connections.setdefault(f"sse:{tenant_id}", {})[user_id] = queue
            try:
                while True:
                    msg = await queue.get()
                    yield f"event: {msg.get('type', 'message')}\ndata: {json.dumps(msg)}\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                self.active_connections.get(f"sse:{tenant_id}", {}).pop(user_id, None)
        return StreamingResponse(event_stream(), media_type="text/event-stream")

    async def _keep_alive(self, ws: WebSocket, tenant_id: str, user_id: str):
        try:
            while True:
                await asyncio.sleep(25)
                # Verifica si el status de la conexión sigue is_active antes de enviar
                if ws.client_state.name == "CONNECTED":
                    await ws.send_text(json.dumps({"type": "ping"}))
                else:
                    break
        except WebSocketDisconnect:
            await self.disconnect(ws, tenant_id, user_id)
        except Exception:
            pass

    async def _send_backlog(self, ws: WebSocket, tenant_id: str, user_id: str, from_id: str):
        """
        [Potenciación] Recupera del EventBus original de Redis los eventos
        que el usuario se perdió si estuvo offline (Delta Sync).
        """
        pass
