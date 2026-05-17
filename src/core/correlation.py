"""
Correlation Tracing Middleware

Garantiza que todos los eventos dentro de un mismo flujo de negocio compartan
el mismo correlation_id. Esto permite:

  - Debugging serio: reconstruir el flujo completo de un lead → quote → payment
  - Analytics: medir duración de ciclos de venta end-to-end
  - Replay: reproducir un flujo completo para testing
  - Session reconstruction: timeline completa de una conversación

Propagación automática:
  - HTTP: X-Correlation-ID header (in/out)
  - EventBus: correlation_id se propaga del evento padre al hijo
  - Redis: stored per-request en contextvars (no threadlocal, safe para async)
"""

import uuid
import logging
from contextvars import ContextVar
from typing import Optional
from uuid import UUID
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# ContextVar para propagación segura en contextos async (coroutine-local, no threadlocal)
_correlation_id_var: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
_causation_id_var: ContextVar[Optional[str]] = ContextVar("causation_id", default=None)

CORRELATION_HEADER = "X-Correlation-ID"
CAUSATION_HEADER = "X-Causation-ID"


# =============================================================================
# Acceso al contexto de tracing (desde cualquier parte del código)
# =============================================================================

def get_correlation_id() -> Optional[UUID]:
    """Retorna el correlation_id is_active en este contexto async."""
    val = _correlation_id_var.get()
    if val:
        try:
            return UUID(val)
        except ValueError:
            return None
    return None


def get_causation_id() -> Optional[UUID]:
    """Retorna el causation_id is_active (ID del evento que causó este)."""
    val = _causation_id_var.get()
    if val:
        try:
            return UUID(val)
        except ValueError:
            return None
    return None


def set_correlation_id(correlation_id: UUID):
    """Establece manualmente el correlation_id (útil en workers async)."""
    _correlation_id_var.set(str(correlation_id))


def set_causation_id(causation_id: UUID):
    """Establece manualmente el causation_id."""
    _causation_id_var.set(str(causation_id))


def new_correlation_id() -> UUID:
    """Genera un nuevo correlation_id y lo establece en el contexto actual."""
    cid = uuid.uuid4()
    _correlation_id_var.set(str(cid))
    return cid


def propagate_from_event(parent_event_id: UUID, parent_correlation_id: Optional[UUID]):
    """
    Propaga correlation_id desde un evento padre al contexto actual.
    Llamar desde los handlers del EventBus al procesar un evento.

    El evento padre es el causation_id del evento hijo.
    """
    # Si el padre ya tiene correlation_id, usarlo; si no, el ID del padre es el nuevo root
    cid = parent_correlation_id or parent_event_id
    _correlation_id_var.set(str(cid))
    _causation_id_var.set(str(parent_event_id))


# =============================================================================
# FastAPI Middleware
# Inyecta/extrae correlation_id en cada request HTTP.
# =============================================================================

class CorrelationMiddleware(BaseHTTPMiddleware):
    """
    Middleware que:
      1. Lee X-Correlation-ID del request (si viene del cliente/gateway)
      2. Si no existe, genera uno nuevo
      3. Lo almacena en ContextVar para toda la request
      4. Lo devuelve en el response header

    Con esto, TODOS los eventos generados durante un request HTTP comparten
    automáticamente el mismo correlation_id sin pasarlo manualmente.
    """

    async def dispatch(self, request: Request, call_next):
        # Leer correlation_id entrante (e.g., del API gateway o cliente)
        incoming = request.headers.get(CORRELATION_HEADER)
        if incoming:
            try:
                cid = str(UUID(incoming))  # Validar que es UUID válido
            except ValueError:
                cid = str(uuid.uuid4())
                logger.debug(f"Invalid X-Correlation-ID received, generated new: {cid}")
        else:
            cid = str(uuid.uuid4())

        # Establecer en ContextVar para este contexto async
        token = _correlation_id_var.set(cid)

        try:
            response: Response = await call_next(request)
        finally:
            _correlation_id_var.reset(token)

        # Propagar en response header (útil para debugging y frontend)
        response.headers[CORRELATION_HEADER] = cid
        return response
