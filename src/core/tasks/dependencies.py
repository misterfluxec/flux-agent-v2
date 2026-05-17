import logging
from fastapi import FastAPI
from .emitter import ProgressEmitter
from core.events.bus import EventBus
from api.telemetry.broadcaster import TelemetryBroadcaster

logger = logging.getLogger(__name__)

def setup_telemetry_broadcaster(app: FastAPI):
    """
    Registra el broadcaster en el ciclo de vida de FastAPI.
    Debe llamarse después de que el EventBus esté inicializado.
    """
    if not hasattr(app.state, "event_bus"):
        logger.warning("EventBus no encontrado en app.state. Telemetría no será propagada a WS.")
        return
        
    broadcaster = TelemetryBroadcaster(app.state.event_bus)
    ProgressEmitter.register_listener(broadcaster.broadcast)
    
    # Lo guardamos en el state para evitar recolección de basura
    app.state.telemetry_broadcaster = broadcaster
    logger.info("📡 TelemetryBroadcaster registrado en ProgressEmitter")

