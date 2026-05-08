import json
from src.domain.events import DomainEvent, EventType
from src.core.realtime_gateway import RealtimeGateway

class WSRealtimeBridge:
    """
    Subscriber especializado que transforma eventos del Bus
    en mensajes WebSocket para el frontend React.
    """
    
    # Mapeo: EventType → Tipo de mensaje UI
    UI_MAPPING = {
        EventType.LEAD_QUALIFIED: "LEAD_HOT",
        EventType.HANDOFF_REQUESTED: "CONVERSATION_HANDOFF",
        EventType.VOICE_TRANSCRIPTION_CHUNK: "VOICE_LIVE_TRANSCRIPT",
        EventType.AGENT_INTERRUPTED: "VOICE_INTERRUPTED",
        EventType.ALERT_IA_DETECTED: "SYSTEM_ALERT",
        EventType.ORCHESTRATOR_STEP_COMPLETED: "ORCHESTRATOR_STEP",
        EventType.BILLING_ALERT: "BILLING_ALERT",
    }
    
    def __init__(self, ws_manager: RealtimeGateway):
        self.ws_manager = ws_manager
    
    async def route_event(self, event: DomainEvent) -> None:
        """Filtra y emite solo los eventos que la UI necesita ver en tiempo real"""
        ui_type = self.UI_MAPPING.get(event.metadata.event_type)
        if not ui_type:
            return  # Ignorar eventos internos (billing, analytics puro, etc.)
            
        payload = {
            "type": ui_type,
            "event_id": str(event.metadata.event_id),
            "timestamp": event.metadata.timestamp.isoformat(),
            "data": event.payload.model_dump()
        }
        
        # Emitir a todos los sockets conectados de ese tenant
        await self.ws_manager.broadcast_to_tenant(
            tenant_id=str(event.metadata.tenant_id),
            message=payload
        )
    
    def register(self, event_bus) -> None:
        """Registra el bridge en el Event Bus"""
        import asyncio
        listened_events = list(self.UI_MAPPING.keys())
        
        asyncio.create_task(
            event_bus.subscribe(
                event_types=listened_events,
                handler=self.route_event,
                consumer_name="ws-bridge",
            )
        )
