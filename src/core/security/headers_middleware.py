"""
Security Headers Middleware for FastAPI
Injects production-grade HTTP security headers on every response.
Compliant with OWASP Secure Headers recommendations.
"""
from fastapi import Request, Response
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.datastructures import MutableHeaders
from typing import Optional


class SecurityHeadersMiddleware:
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
        app: ASGIApp,
        hsts_max_age: int = 31536000,  # 1 año en segundos
        csp_policy: Optional[str] = None,
        enable_xss_protection: bool = True,
        is_production: bool = False,
    ):
        self.app = app
        self.hsts_max_age = hsts_max_age
        self.is_production = is_production
        self.enable_xss_protection = enable_xss_protection

        # CSP: restrictiva en producción, permisiva en desarrollo
        if csp_policy:
            self.csp_policy = csp_policy
        elif is_production:
            self.csp_policy = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            )
        else:
            self.csp_policy = (
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' *; "
                "frame-ancestors 'none'"
            )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                
                # 🔒 Anti-Clickjacking
                headers["X-Frame-Options"] = "DENY"
                
                # 🔒 Anti-MIME-Sniffing
                headers["X-Content-Type-Options"] = "nosniff"
                
                # 🔒 HSTS
                headers["Strict-Transport-Security"] = (
                    f"max-age={self.hsts_max_age}; includeSubDomains; preload"
                )
                
                # 🔒 Content Security Policy
                headers["Content-Security-Policy"] = self.csp_policy
                
                # 🔒 Referrer Policy
                headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
                
                # 🔒 Permissions Policy
                headers["Permissions-Policy"] = (
                    "geolocation=(), microphone=(), camera=(), payment=(), "
                    "usb=(), magnetometer=(), gyroscope=(), accelerometer=()"
                )
                
                # 🔒 Legacy XSS Protection
                if self.enable_xss_protection:
                    headers["X-XSS-Protection"] = "1; mode=block"
                
                # 🔒 Eliminar headers que revelan versión del servidor
                if "server" in headers:
                    del headers["server"]
                if "x-powered-by" in headers:
                    del headers["x-powered-by"]

            await send(message)

        await self.app(scope, receive, send_wrapper)
