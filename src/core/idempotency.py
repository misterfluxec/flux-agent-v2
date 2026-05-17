import hashlib
import logging
from contextvars import ContextVar
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

_idempotency_key_var: ContextVar[Optional[str]] = ContextVar("idempotency_key", default=None)
IDEMPOTENCY_HEADER = "Idempotency-Key"

def get_idempotency_key() -> Optional[str]:
    """Retorna el idempotency_key is_active en este contexto async."""
    return _idempotency_key_var.get()

def set_idempotency_key(key: str):
    """Establece manualmente el idempotency_key."""
    _idempotency_key_var.set(key)

class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware que asegura que cada petición mutativa tenga un idempotency_key.
    Si el cliente no lo envía en el header, genera uno basado en hash de la petición
    como fallback durante la fase Beta.
    """
    async def dispatch(self, request: Request, call_next):
        # Solo procesamos mutaciones
        if request.method not in ["POST", "PUT", "PATCH", "DELETE"]:
            return await call_next(request)
            
        idem_key = request.headers.get(IDEMPOTENCY_HEADER)
        
        if not idem_key:
            # Estrategia de fallback (Hash) para la Fase Beta
            try:
                body = await request.body()
                
                # Restaurar el cuerpo de la petición para los siguientes middlewares/rutas
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive
                
                tenant_id = request.headers.get("X-Tenant-ID", "unknown_tenant")
                auth_header = request.headers.get("Authorization", "no_auth")
                
                # hash(tenant_id + route + normalized_payload + auth)
                hash_input = f"{tenant_id}:{request.url.path}:{body.decode('utf-8', errors='ignore')}:{auth_header}"
                idem_key = f"auto_{hashlib.sha256(hash_input.encode()).hexdigest()}"
                
            except Exception as e:
                logger.warning(f"Error generando idempotency key fallback: {e}")
                idem_key = None
                
        if idem_key:
            token = _idempotency_key_var.set(idem_key)
            try:
                response = await call_next(request)
            finally:
                _idempotency_key_var.reset(token)
            
            response.headers[IDEMPOTENCY_HEADER] = idem_key
            return response
        else:
            return await call_next(request)
