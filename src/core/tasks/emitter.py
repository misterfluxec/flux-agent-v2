import json
import logging
from typing import Any, Callable, Dict, List
import traceback

logger = logging.getLogger(__name__)

class ProgressEmitter:
    """
    Emisor agnóstico de eventos de progreso para tareas en segundo plano.
    Mantiene un registro de listeners (como el TelemetryBroadcaster) que
    se encargarán de distribuir los eventos (vía Redis, WebSockets, etc.).
    """
    
    _listeners: List[Callable[[str, Dict[str, Any]], Any]] = []

    @classmethod
    def register_listener(cls, listener: Callable[[str, Dict[str, Any]], Any]):
        if listener not in cls._listeners:
            cls._listeners.append(listener)
            
    @classmethod
    def unregister_listener(cls, listener: Callable[[str, Dict[str, Any]], Any]):
        if listener in cls._listeners:
            cls._listeners.remove(listener)

    @classmethod
    async def emit(cls, event_type: str, payload: Dict[str, Any]):
        """
        Emite un evento a todos los listeners registrados.
        Las tareas de fondo usan esto de forma desacoplada.
        """
        if not cls._listeners:
            # Si no hay listeners, simplemente lo logeamos en debug
            logger.debug(f"[ProgressEmitter] Sin listeners para {event_type} - {payload}")
            return
            
        for listener in cls._listeners:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(listener):
                    await listener(event_type, payload)
                else:
                    listener(event_type, payload)
            except Exception as e:
                logger.error(f"[ProgressEmitter] Error en listener: {e}", exc_info=True)
