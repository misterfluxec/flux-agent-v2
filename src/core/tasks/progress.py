# =============================================================================
# FLUXAGENT V2 — EMISOR DE PROGRESO AGNÓSTICO
# =============================================================================
# Emite eventos de progreso sin conocer la infraestructura de transporte.
# =============================================================================

import logging
from typing import Callable, Any, List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ProgressEvent:
    task_id: str
    tenant_id: str
    percentage: int
    step: str
    message: str
    status: str
    payload: Dict[str, Any]

class ProgressEmitter:
    """
    Sistema de pub-sub interno para eventos de progreso.
    Cualquier infraestructura (Redis, WS) puede suscribirse.
    """
    def __init__(self):
        self._subscribers: List[Callable[[ProgressEvent], Any]] = []

    def subscribe(self, callback: Callable[[ProgressEvent], Any]):
        self._subscribers.append(callback)

    async def emit(self, event: ProgressEvent):
        """Notifica a todos los suscriptores de forma asíncrona."""
        for subscriber in self._subscribers:
            try:
                import asyncio
                if asyncio.iscoroutinefunction(subscriber):
                    await subscriber(event)
                else:
                    subscriber(event)
            except Exception as e:
                logger.error(f"Error en suscriptor de progreso: {e}")

# Instancia global para el bridge
progress_emitter = ProgressEmitter()

async def report_progress(
    percentage: Optional[int] = None,
    step: str = "processing",
    message: str = "",
    status: str = "processing",
    payload: Optional[Dict[str, Any]] = None
):
    """
    Helper global que detecta el task_id y tenant_id del contexto
    y emite un evento de progreso.
    """
    from .context import get_current_task_id, get_current_tenant_id
    
    task_id = get_current_task_id()
    tenant_id = get_current_tenant_id()
    
    if task_id and tenant_id:
        event = ProgressEvent(
            task_id=task_id,
            tenant_id=str(tenant_id),
            percentage=percentage if percentage is not None else 0, # El runner manejará la acumulación
            step=step,
            message=message,
            status=status,
            payload=payload or {}
        )
        await progress_emitter.emit(event)
