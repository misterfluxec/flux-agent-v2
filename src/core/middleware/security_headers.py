"""
Security Headers Middleware — FluxAgent V2
==========================================
Inyecta headers HTTP de seguridad en todas las respuestas.
Estándar bancario: HSTS, CSP, X-Frame-Options, Permissions-Policy, etc.

Referencia: OWASP Secure Headers Project
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import os


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware que añade headers de seguridad HTTP a todas las respuestas.
    Cumple con: OWASP, PCI DSS nivel básico, y buenas prácticas bancarias.
    """

    def __init__(self, app: ASGIApp, is_production: bool = False):
        super().__init__(app)
        self.is_production = is_production or os.getenv("APP_ENV", "development") == "production"

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)

        # ─── Clickjacking Protection ───
        response.headers["X-Frame-Options"] = "DENY"

        # ─── MIME Sniffing Protection ───
        response.headers["X-Content-Type-Options"] = "nosniff"

        # ─── XSS Protection (legacy browsers) ───
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # ─── Referrer Policy ───
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # ─── Permissions Policy (disable dangerous APIs) ───
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )

        # ─── Content Security Policy ───
        # Permisiva en dev, estricta en producción
        if self.is_production:
            csp = (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' wss: https:; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self';"
            )
        else:
            # Dev: más permisiva para evitar bloqueos con hot-reload
            csp = "default-src 'self' 'unsafe-inline' 'unsafe-eval' *; frame-ancestors 'none';"

        response.headers["Content-Security-Policy"] = csp

        # ─── HSTS (solo en producción con HTTPS) ───
        if self.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # ─── Server Header Removal (no revelar stack) ───
        response.headers.pop("server", None)
        response.headers.pop("x-powered-by", None)

        # ─── Cache Control para APIs sensibles ───
        if request.url.path.startswith("/api/v1/auth"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"

        return response
