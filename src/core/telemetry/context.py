# =============================================================================
# FLUXAGENT V2 — CONTEXTO DE TELEMETRÍA UNIFICADO
# =============================================================================
# Gestión de correlation_id, causation_id y propagación distribuida.
# Reemplaza y unifica core.correlation y core.observability.context.
# =============================================================================

from contextvars import ContextVar
from typing import Optional
from uuid import UUID
import uuid

# ContextVars para propagación segura en hilos/corutinas
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
causation_id_ctx: ContextVar[Optional[str]] = ContextVar("causation_id", default=None)

def set_correlation_id(cid: Optional[str] = None) -> str:
    """Establece o genera un correlation_id."""
    val = cid or str(uuid.uuid4())
    correlation_id_ctx.set(val)
    return val

def get_correlation_id() -> str:
    """Retorna el correlation_id actual."""
    return correlation_id_ctx.get() or str(uuid.uuid4()) # Fallback a uno nuevo si no hay contexto

def set_causation_id(cid: str):
    """Establece el ID del evento que causó la acción actual."""
    causation_id_ctx.set(cid)

def get_causation_id() -> Optional[str]:
    """Retorna el causation_id actual."""
    return causation_id_ctx.get()

def propagate_context(correlation_id: str, causation_id: Optional[str] = None):
    """Propaga el contexto completo (útil para workers/eventos)."""
    correlation_id_ctx.set(correlation_id)
    if causation_id:
        causation_id_ctx.set(causation_id)
