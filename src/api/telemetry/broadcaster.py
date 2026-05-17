import json
import logging
from typing import Any, Dict
from core.events.bus import EventBus
from core.events.types import Event, EventType
from api.telemetry.schema import ProgressEvent

logger = logging.getLogger(__name__)

class BusinessTranslator:
    """Mapea eventos crudos técnicos a lenguaje de negocio (Auditoría)"""
    @staticmethod
    def translate(event_type: str, payload: Dict[str, Any]) -> str:
        label = payload.get("label", "Proceso")
        if event_type == "task_started":
            return "Iniciando nueva tarea en segundo plano..."
        elif event_type == "task_step_started":
            return f"Iniciando paso: {label}."
        elif event_type == "task_step_completed":
            duration = payload.get("duration_ms", 0)
            return f"Paso completado: {label} (en {duration}ms)."
        elif event_type == "task_step_failed":
            error = payload.get("error", "Error desconocido")
            return f"Fallo en paso: {label}. Motivo: {error}"
        elif event_type == "task_completed":
            return "Tarea completada exitosamente."
        elif event_type == "task_failed":
            error = payload.get("error", "Error desconocido")
            return f"La tarea falló de forma crítica. Motivo: {error}"
        return f"Evento interno: {event_type}"

class TelemetryBroadcaster:
    """
    Escucha al ProgressEmitter y publica eventos estandarizados
    (ProgressEvent) al EventBus para consumo del WS en Frontend.
    """
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def broadcast(self, event_type: str, payload: Dict[str, Any]):
        try:
            tenant_id = payload.get("tenant_id", "system")
            task_id = payload.get("task_id", "unknown")
            
            # 1. Empaquetar como ProgressEvent (Validación de contrato)
            # Mapeamos tipos de emitter a tipos de ProgressEvent
            ws_event_type = event_type
            if ws_event_type == "task_step_started": ws_event_type = "step_started"
            if ws_event_type == "task_step_completed": ws_event_type = "step_completed"
            if ws_event_type == "task_step_failed": ws_event_type = "step_failed"

            # Inyectar traducción de negocio (AuditTrail)
            payload["human_message"] = BusinessTranslator.translate(event_type, payload)

            progress_event = ProgressEvent(
                event_type=ws_event_type,
                task_id=task_id,
                data=payload
            )

            # 2. Publicar en el EventBus de la App
            event = Event(
                type=EventType.SYSTEM_ALERT, 
                payload={
                    "type": "telemetry",
                    "event": progress_event.model_dump(mode='json')
                },
                tenant_id=tenant_id,
                channel=f"task:{task_id}"
            )
            
            await self.event_bus.publish(event)
            logger.debug(f"[TelemetryBroadcaster] {ws_event_type} emitido para task {task_id}")
            
        except Exception as e:
            logger.error(f"[TelemetryBroadcaster] Error al emitir telemetría: {e}", exc_info=True)
