import logging
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI
from slowapi.middleware import SlowAPIMiddleware
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

def get_real_ip(request):
    """Obtener IP real incluso detrás de proxies (Cloudflare, Nginx)"""
    # Prefer X-Forwarded-For si está presente
    if "x-forwarded-for" in request.headers:
        # Puede tener múltiples IPs separadas por coma, la primera es el cliente original
        return request.headers["x-forwarded-for"].split(",")[0].strip()
    return get_remote_address(request)

# Inicializar Redis URI desde entorno o configuración
redis_uri = os.getenv("REDIS_URL", config.redis_url)

# Instancia global del limitador
limiter = Limiter(
    key_func=get_real_ip,
    default_limits=["1000/minute"], # Límite global por defecto
    storage_uri=redis_uri,
    strategy="fixed-window"
)

def setup_rate_limiting(app: FastAPI):
    """Configurar SlowAPI con backend de Redis en FastAPI"""
    # Adjuntar limiter al estado de la aplicación (requerido por SlowAPI)
    app.state.limiter = limiter
    
    # Manejador global de excepciones para 429 Too Many Requests
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # Middleware para interceptar requests y aplicar límites definidos a nivel global o router
    app.add_middleware(SlowAPIMiddleware)
    
    logger.info(f"✅ Rate Limiting (SlowAPI) configurado con almacenamiento Redis: {redis_uri}")
