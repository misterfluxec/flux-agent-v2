"""
Security Headers Middleware for FastAPI
Injects production-grade HTTP security headers on every response.
Compliant with OWASP Secure Headers recommendations.
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from typing import Optional


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que inyecta headers de seguridad en todas las respuestas HTTP.
    
    Headers aplicados:
    - X-Frame-Options: DENY → Previene clickjacking
    - X-Content-Type-Options: nosniff → Previene MIME sniffing
    - Strict-Transport-Security: HSTS forzado con includeSubDomains
    - Content-Security-Policy: Política restrictiva por defecto
    - Referrer-Policy: Limita información de referencia
    - Permissions-Policy: Deshabilita APIs sensibles
    - X-XSS-Protection: Legacy pero útil para browsers antiguos
    """
    
    def __init__(
        self,
        app,
        hsts_max_age: int = 31536000,  # 1 año en segundos
        csp_policy: Optional[str] = None,
        enable_xss_protection: bool = True,
    ):
        super().__init__(app)
        self.hsts_max_age = hsts_max_age
        self.csp_policy = csp_policy or (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' ws: wss:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        self.enable_xss_protection = enable_xss_protection

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        response = await call_next(request)
        
        # 🔒 Anti-Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # 🔒 Anti-MIME-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # 🔒 HSTS (solo en producción, el middleware se registra condicionalmente)
        response.headers["Strict-Transport-Security"] = (
            f"max-age={self.hsts_max_age}; includeSubDomains; preload"
        )
        
        # 🔒 Content Security Policy
        response.headers["Content-Security-Policy"] = self.csp_policy
        
        # 🔒 Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # 🔒 Permissions Policy (deshabilita APIs sensibles por defecto)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), "
            "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
        )
        
        # 🔒 Legacy XSS Protection (aún útil para browsers antiguos)
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # 🔒 Eliminar header que revela versión del servidor
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]
        
        return response
