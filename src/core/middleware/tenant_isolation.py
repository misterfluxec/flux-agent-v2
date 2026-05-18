# =============================================================================
# FLUXAGENT V2 — TENANT ISOLATION MIDDLEWARE
# =============================================================================
# Aplica RLS automáticamente para cada request autenticado
# Previene fugas de datos entre tenants
# =============================================================================

import logging
import time
import uuid
from typing import Callable
from fastapi import Request, HTTPException, status
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import MutableHeaders

from auth import get_tenant_actual_opcional
from core.security.headers_middleware import SecurityHeadersMiddleware  # noqa: F401 — re-exportado

logger = logging.getLogger(__name__)

class TenantIsolationMiddleware:
    """Middleware que aplica aislamiento Multi-Tenant (extrae e inyecta tenant_id)"""
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        ]
        
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope["path"]
        if self._should_exclude_path(path) or not path.startswith("/api"):
            await self.app(scope, receive, send)
            return

        # Asegurar inicialización de state
        scope["state"] = scope.get("state", {})
        request_id = scope["state"].get("request_id") or str(uuid.uuid4())
        scope["state"]["request_id"] = request_id

        start_time = time.time()
        
        try:
            request = Request(scope, receive)
            tenant_id = await self._extract_tenant_id(request)
            
            if tenant_id:
                scope["state"]["tenant_id"] = tenant_id
                logger.info(
                    f"[{request_id}] {scope['method']} {path} "
                    f"- Tenant: {tenant_id}"
                )
            else:
                logger.info(
                    f"[{request_id}] {scope['method']} {path} "
                    f"- Sin tenant (público)"
                )
            
            await self.app(scope, receive, send)
                
        except Exception as e:
            logger.error(
                f"[{request_id}] Error en middleware tenant isolation: {e}",
                exc_info=True
            )
            await send({
                "type": "http.response.start",
                "status": 500,
                "headers": [(b"content-type", b"application/json")]
            })
            await send({
                "type": "http.response.body",
                "body": b'{"error": "error_interno", "mensaje": "Error procesando solicitud"}'
            })
        finally:
            duration = time.time() - start_time
            logger.info(
                f"[{request_id}] Request completado en {duration:.3f}s"
            )
    
    def _should_exclude_path(self, path: str) -> bool:
        """Determina si el path debe excluirse del middleware"""
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        return False
    
    async def _extract_tenant_id(self, request: Request) -> str:
        """Extrae tenant_id del request desde múltiples fuentes"""
        
        # 1. Desde headers (para requests externos)
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            return tenant_id
        
        # 2. Desde token JWT (inyectado por auth middleware)
        if hasattr(request.state, 'tenant_id'):
            return request.state.tenant_id
        
        # 3. Desde query param (solo para desarrollo/testing)
        if "tenant_id" in request.query_params:
            tenant_id = request.query_params["tenant_id"]
            logger.warning(f"Usando tenant_id desde query param: {tenant_id}")
            return tenant_id
        
        # 4. Intentar obtener desde auth (si el request ya está autenticado)
        try:
            from auth import get_tenant_actual_opcional
            tenant_data = await get_tenant_actual_opcional(request)
            if tenant_data:
                return tenant_data.tenant_id
        except Exception:
            pass
        
        return None

class RequestLoggingMiddleware:
    """Middleware para logging detallado de requests"""
    
    def __init__(self, app: ASGIApp, exclude_paths: list = None):
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/health",
            "/favicon.ico"
        ]
        
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["path"] in self.exclude_paths:
            await self.app(scope, receive, send)
            return
            
        start_time = time.time()
        path = scope["path"]
        method = scope["method"]
        
        logger.info(f"📥 {method} {path}")
        
        scope["state"] = scope.get("state", {})
        request_id = scope["state"].get("request_id") or str(uuid.uuid4())
        scope["state"]["request_id"] = request_id

        async def send_wrapper(message: dict) -> None:
            if message["type"] == "http.response.start":
                duration = time.time() - start_time
                status_code = message["status"]
                logger.info(
                    f"📤 {status_code} {method} {path} "
                    f"- Duration: {duration:.3f}s"
                )
                headers = MutableHeaders(scope=message)
                headers["X-Request-ID"] = request_id
                headers["X-Response-Time"] = f"{duration:.3f}"
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ {method} {path} "
                f"- Error: {e} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise

# Helper para registrar middlewares en main.py
def setup_middlewares(app):
    """Configura todos los middlewares en sort_order correcto."""
    from config import obtener_config
    _cfg = obtener_config()

    # 1. Security headers canónicos con CSP diferenciada por entorno
    app.add_middleware(SecurityHeadersMiddleware, is_production=_cfg.es_produccion)

    # 2. Request logging
    app.add_middleware(RequestLoggingMiddleware)

    # 3. Tenant isolation (más importante)
    app.add_middleware(TenantIsolationMiddleware)

    logger.info("✅ Middlewares: SecurityHeaders(prod=%s), Logging, TenantIsolation", _cfg.es_produccion)
