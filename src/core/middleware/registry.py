import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import obtener_config
from core.security.headers_middleware import SecurityHeadersMiddleware
from core.middleware.tenant_isolation import TenantIsolationMiddleware, RequestLoggingMiddleware
from core.correlation import CorrelationMiddleware
from core.exception_handlers import setup_exception_handlers
from core.security.rate_limiter import setup_rate_limiting

logger = logging.getLogger(__name__)
config = obtener_config()

def setup_middlewares(app: FastAPI):
    # 0. Limite de Tasa (SlowAPI via Redis)
    setup_rate_limiting(app)

    # 1. Excepciones (capturan todo lo que no se maneje)
    setup_exception_handlers(app)

    # 2. Seguridad HTTP (Headers OWASP/bancarios)
    app.add_middleware(SecurityHeadersMiddleware, is_production=config.es_produccion)

    # 3. Correlation ID (propaga X-Correlation-ID en todos los logs)
    app.add_middleware(CorrelationMiddleware)

    # 4. Request Logging (loguea entrada/salida de requests)
    app.add_middleware(RequestLoggingMiddleware)

    # 5. Aislamiento Multi-Tenant (RLS automático por tenant)
    app.add_middleware(TenantIsolationMiddleware)

    # 6. CORS (debe ir al final para aplicarse primero en el stack Starlette)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    logger.info("✅ Middlewares registrados en orden correcto")
