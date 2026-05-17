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
from fastapi.responses import Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from database import obtener_sesion
from auth import get_tenant_actual_opcional

logger = logging.getLogger(__name__)

class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """Middleware que aplica RLS automáticamente para cada request"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Procesa request aplicando RLS si es necesario"""
        
        # Generar ID único para request (tracing)
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Excluir paths públicos
        if self._should_exclude_path(request.url.path):
            return await call_next(request)
        
        # Solo aplicar a rutas de API
        if not request.url.path.startswith("/api"):
            return await call_next(request)
        
        start_time = time.time()
        
        try:
            # Obtener tenant del request (inyectado por auth)
            tenant_id = await self._extract_tenant_id(request)
            
            if tenant_id:
                # Aplicar RLS y continuar
                async with obtener_sesion() as db:
                    await self._apply_rls(db, tenant_id)
                    request.state.db = db
                    request.state.tenant_id = tenant_id
                    
                    # Log de request con tenant context
                    logger.info(
                        f"[{request_id}] {request.method} {request.url.path} "
                        f"- Tenant: {tenant_id}"
                    )
                    
                    try:
                        response = await call_next(request)
                        return response
                    finally:
                        await db.close()
            else:
                # Request sin tenant (ej: login)
                logger.info(
                    f"[{request_id}] {request.method} {request.url.path} "
                    f"- Sin tenant (público)"
                )
                return await call_next(request)
                
        except Exception as e:
            logger.error(
                f"[{request_id}] Error en middleware tenant isolation: {e}",
                exc_info=True
            )
            return Response(
                content='{"error": "error_interno", "mensaje": "Error procesando solicitud"}',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                media_type="application/json"
            )
        finally:
            # Log de tiempo de respuesta
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
            tenant_data = await get_tenant_actual_opencial(request)
            if tenant_data:
                return tenant_data.tenant_id
        except Exception:
            pass
        
        return None
    
    async def _apply_rls(self, db: AsyncSession, tenant_id: str):
        """Aplica RLS de forma segura y consistente"""
        try:
            # Usar SET LOCAL para que solo afecte esta transacción
            await db.execute(
                text("SET LOCAL app.current_tenant_id = :tid"),
                {"tid": tenant_id}
            )
            
            # Verificar que se aplicó correctamente
            result = await db.execute(
                text("SELECT current_setting('app.current_tenant_id')")
            )
            current_setting = result.scalar()
            
            if current_setting != tenant_id:
                logger.error(
                    f"RLS no se aplicó correctamente. "
                    f"Esperado: {tenant_id}, Actual: {current_setting}"
                )
                raise Exception("Error aplicando RLS")
            
            logger.debug(f"RLS aplicado correctamente para tenant: {tenant_id}")
            
        except Exception as e:
            logger.error(f"Error aplicando RLS: {e}")
            raise

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware para logging detallado de requests"""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/health",
            "/favicon.ico"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Loguea request y response"""
        
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        start_time = time.time()
        
        # Log de request
        logger.info(
            f"📥 {request.method} {request.url.path} "
            f"- Headers: {dict(request.headers)}"
        )
        
        try:
            response = await call_next(request)
            
            # Log de response
            duration = time.time() - start_time
            logger.info(
                f"📤 {response.status_code} {request.method} {request.url.path} "
                f"- Duration: {duration:.3f}s"
            )
            
            # Agregar headers de respuesta
            response.headers["X-Request-ID"] = getattr(
                request.state, 'request_id', 'unknown'
            )
            response.headers["X-Response-Time"] = f"{duration:.3f}"
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"❌ {request.method} {request.url.path} "
                f"- Error: {e} - Duration: {duration:.3f}s",
                exc_info=True
            )
            raise

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware para headers de seguridad"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Agrega headers de seguridad"""
        
        response = await call_next(request)
        
        # Headers de seguridad
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Headers de cache para APIs
        if request.url.path.startswith("/api"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

# Helper para registrar middlewares en main.py
def setup_middlewares(app):
    """Configura todos los middlewares en sort_order correcto"""
    
    # 1. Security headers (primero)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 2. Request logging
    app.add_middleware(RequestLoggingMiddleware)
    
    # 3. Tenant isolation (más importante)
    app.add_middleware(TenantIsolationMiddleware)
    
    logger.info("✅ Middlewares configurados: Security, Logging, Tenant Isolation")
