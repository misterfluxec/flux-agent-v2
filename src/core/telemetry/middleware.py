# =============================================================================
# FLUXAGENT V2 — TELEMETRY MIDDLEWARE (UNIFIED)
# =============================================================================
# Punto de entrada de trazabilidad para cada request HTTP.
# =============================================================================

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from .context import set_correlation_id
from .logger import get_logger

logger = get_logger("core.telemetry.middleware")

class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        
        # 1. Extraer o generar Correlation ID
        cid = request.headers.get("X-Correlation-ID") or request.headers.get("X-Request-ID")
        correlation_id = set_correlation_id(cid)
        
        # 2. Log de inicio de request (Agnóstico a la ruta por ahora)
        logger.debug(f"Iniciando {request.method} {request.url.path}", method=request.method, path=request.url.path)
        
        try:
            response = await call_next(request)
            
            # 3. Calcular duración
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            # 4. Log de finalización enriquecido
            logger.info(
                f"Finalizado {request.method} {request.url.path} - {response.status_code}",
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2)
            )
            
            # 5. Propagar al cliente
            response.headers["X-Correlation-ID"] = correlation_id
            return response
            
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Fallo en {request.method} {request.url.path}",
                error=e,
                duration_ms=round(duration_ms, 2)
            )
            raise e
