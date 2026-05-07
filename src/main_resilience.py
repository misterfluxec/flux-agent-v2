# =============================================================================
# FLUXAGENT V2 — MAIN CON RESILIENCIA
# =============================================================================
# Versión de main.py con patrones de resiliencia aplicados
# Bulkhead, Circuit Breakers, Timeouts y Retry unificados
# =============================================================================

import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

# Configuración y componentes base
from config import obtener_config
from database import cerrar_db, configurar_rls, inicializar_db
from auth import get_tenant_actual_opcional

# Resiliencia
from services.resilient_services import initialize_resilience

# Cache y Rate Limiting (existente)
from core.cache.client import initialize_cache, cleanup_cache
from core.rate_limit.middleware import create_rate_limit_middleware

# Observabilidad (existente)
from core.observability.metrics import get_metrics
from core.observability.logging import get_logger, set_request_context, clear_request_context
from core.observability.tracing import get_tracing_manager

# Routers existentes
from routers.auth_router import router as auth_router
from routers.stats_router import router as stats_router
from routers.products_router import router as products_router
from routers.whatsapp_router import router as whatsapp_router
from routers.webhooks_router import router as webhooks_router
from routers.leads_router import router as leads_router
from routers.admin_router import router as admin_router
from routers.users_router import router as users_router
from routers.agents_router import router as agents_router
from routers.payments_router import router as payments_router
from routers.ingest_router import router as ingest_router
from routers.voice_router import router as voice_router
from routers.channels_router import router as channels_router
from routers.whatsapp_health_router import router as whatsapp_health_router
from routers.whatsapp_cloud_router import router as whatsapp_cloud_router
from routers.quota_router import router as quota_router
from routers.oauth_sync_router import router as oauth_sync_router
from routers.sync_router import router as sync_router
from routers.upload_router import router as upload_router
from app.routers.sales_agent_router import router as sales_router
from routers.analytics_router_cached import router as analytics_router
from routers.billing_router import router as billing_router
from routers.plans_router import router as plans_router

# Router de resiliencia
from routers.resilience_router import router as resilience_router

logger = logging.getLogger(__name__)
config = obtener_config()

# =============================================================================
# CICLO DE VIDA CON RESILIENCIA
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida con inicialización de resiliencia"""
    
    # Inicializar logging estructurado
    structured_logger = get_logger("lifecycle")
    structured_logger.info("lifecycle", "Iniciando FluxAgent V2 con resiliencia avanzada")
    
    try:
        # Inicializar servicios base
        structured_logger.info("lifecycle", "Inicializando servicios base")
        await inicializar_db()
        
        # Inicializar cache
        structured_logger.info("lifecycle", "Inicializando cache Redis")
        await initialize_cache()
        
        # Inicializar resiliencia
        structured_logger.info("lifecycle", "🛡️ Inicializando resiliencia avanzada")
        await initialize_resilience()
        
        # Inicializar métricas
        structured_logger.info("lifecycle", "📊 Inicializando métricas Prometheus")
        metrics = get_metrics()
        metrics.set_build_info(
            version=config.app_version,
            environment=config.app_env
        )
        
        # Inicializar tracing
        structured_logger.info("lifecycle", "🔍 Inicializando OpenTelemetry tracing")
        tracing = get_tracing_manager()
        
        # Health checks con logging estructurado
        structured_logger.info("lifecycle", "Verificando servicios externos")
        
        # Verificar Redis
        try:
            import redis.asyncio as aioredis
            r = aioredis.from_url(config.redis_url, decode_responses=True)
            await r.ping()
            await r.aclose()
            structured_logger.info("lifecycle", "Redis disponible y conectado")
        except Exception as exc:
            structured_logger.error("lifecycle", "Redis no disponible", error=exc)
        
        # Verificar Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{config.ollama_base_url}/api/tags")
                if resp.status_code == 200:
                    modelos = [m.get("name") for m in resp.json().get("models", [])]
                    structured_logger.info("lifecycle", f"Ollama disponible. Modelos: {modelos}")
        except Exception as exc:
            structured_logger.warning("lifecycle", "Ollama no respondió", error=exc)
        
        structured_logger.info("lifecycle", "✅ FluxAgent V2 listo con resiliencia avanzada")
        
        # Iniciar servidor de métricas Prometheus
        try:
            from core.metrics import start_metrics_server
            start_metrics_server(8001)
            structured_logger.info("lifecycle", "📊 Métricas Prometheus en http://localhost:8001/metrics")
        except Exception as e:
            structured_logger.warning("lifecycle", f"Servidor métricas no iniciado: {e}")
        
        # Iniciar scheduler RAG
        try:
            from tasks.rag_scheduler import start_rag_scheduler, stop_rag_scheduler
            await start_rag_scheduler()
            structured_logger.info("lifecycle", "🔄 Scheduler RAG iniciado")
        except Exception as e:
            structured_logger.warning("lifecycle", f"Scheduler RAG no iniciado: {e}")
        
        yield
        
    except Exception as e:
        structured_logger.critical("lifecycle", "Error crítico en inicialización", error=e)
        raise
    
    finally:
        # Cleanup con logging estructurado
        structured_logger.info("lifecycle", "🔄 Iniciando shutdown de servicios con resiliencia")
        
        try:
            await stop_rag_scheduler()
            structured_logger.info("lifecycle", "🔄 Scheduler RAG detenido")
        except Exception as e:
            structured_logger.warning("lifecycle", f"Error deteniendo scheduler: {e}")
        
        try:
            await cleanup_cache()
            structured_logger.info("lifecycle", "🧹 Cache limpiado")
        except Exception as e:
            structured_logger.warning("lifecycle", f"Error limpiando cache: {e}")
        
        try:
            await cerrar_db()
            structured_logger.info("lifecycle", "🗑️ Base de datos cerrada")
        except Exception as e:
            structured_logger.warning("lifecycle", f"Error cerrando BD: {e}")
        
        # Limpiar resiliencia
        try:
            from core.resilience.bulkhead import get_bulkhead_manager
            from core.resilience.timeout import get_timeout_manager
            from core.resilience.circuit_breaker import get_circuit_breaker
            
            bh_manager = get_bulkhead_manager()
            await bh_manager.shutdown_all()
            
            timeout_manager = get_timeout_manager()
            # Los timeouts no tienen cleanup específico
            
            structured_logger.info("lifecycle", "🛡️ Resiliencia limpiada")
        except Exception as e:
            structured_logger.warning("lifecycle", f"Error limpiando resiliencia: {e}")
        
        structured_logger.info("lifecycle", "🛑 FluxAgent V2 con resiliencia detenido")

# =============================================================================
# CREACIÓN DE LA APLICACIÓN FASTAPI CON RESILIENCIA
# =============================================================================

app = FastAPI(
    title="FluxAgent V2 - Resilience Edition",
    description="Backend multi-tenant para agentes IA con resiliencia avanzada",
    version=config.app_version,
    lifespan=lifespan
)

# =============================================================================
# MIDDLEWARE CON OBSERVABILIDAD INTEGRADA
# =============================================================================

from fastapi.middleware.cors import CORSMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "X-Request-ID"],
)

# Rate Limiting con resiliencia
rate_limit_config = {
    "global_limits": {
        "requests": {"limit": 1000, "window": 3600},
        "analytics": {"limit": 100, "window": 60}
    },
    "tenant_limits": {
        "free": {
            "requests": {"limit": 100, "window": 3600},
            "messages": {"limit": 10, "window": 60}
        },
        "basic": {
            "requests": {"limit": 500, "window": 3600},
            "messages": {"limit": 50, "window": 60}
        },
        "pro": {
            "requests": {"limit": 2000, "window": 3600},
            "messages": {"limit": 200, "window": 60}
        }
    }
}

app.add_middleware(
    create_rate_limit_middleware(
        global_limits=rate_limit_config["global_limits"],
        tenant_limits=rate_limit_config["tenant_limits"]
    )
)

# Middleware de logging estructurado y tracing
@app.middleware("http")
async def observability_middleware(request, call_next):
    """Middleware principal de observabilidad con resiliencia"""
    structured_logger = get_logger("middleware")
    
    # Generar request ID
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Establecer contexto de logging
    tenant_id = await get_tenant_actual_opcional(request)
    set_request_context(
        request_id=request_id,
        tenant_id=tenant_id.tenant_id if tenant_id else None
    )
    
    import time
    start_time = time.time()
    
    try:
        # Log de request con contexto completo
        structured_logger.http_request(
            method=request.method,
            path=request.url.path,
            status_code=200,  # Default, se actualizará después
            duration_ms=0,  # Se calculará después
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "unknown")
        )
        
        # Ejecutar request
        response = await call_next(request)
        
        # Calcular duración
        duration_ms = (time.time() - start_time) * 1000
        
        # Actualizar log con resultado real
        structured_logger.http_request(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            ip_address=request.client.host if request.client else "unknown",
            user_agent=request.headers.get("User-Agent", "unknown")
        )
        
        # Agregar headers de observabilidad
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        response.headers["X-Resilience-Enabled"] = "true"
        
        # Métricas de request
        metrics = get_metrics()
        metrics.increment_requests_total(
            method=request.method,
            endpoint=request.url.path,
            status_code=str(response.status_code),
            tenant_id=tenant_id.tenant_id if tenant_id else "unknown"
        )
        metrics.observe_request_duration(
            duration=duration_ms / 1000,
            method=request.method,
            endpoint=request.url.path,
            tenant_id=tenant_id.tenant_id if tenant_id else "unknown"
        )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        # Log de error con contexto
        structured_logger.http_error(
            method=request.method,
            path=request.url.path,
            status_code=500,
            error=e,
            duration_ms=duration_ms
        )
        
        # Métricas de error
        metrics = get_metrics()
        metrics.increment_errors(
            error_type=type(e).__name__.lower(),
            component="middleware",
            tenant_id=tenant_id.tenant_id if tenant_id else "unknown"
        )
        
        # Tracing del error
        tracing = get_tracing_manager()
        with tracing.create_span("middleware_error") as span:
            span.record_error(e)
            span.set_tag("request_id", request_id)
            span.set_tag("method", request.method)
            span.set_tag("path", request.url.path)
        
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={
                "error": "error_interno",
                "mensaje": "Ocurrió un error inesperado",
                "request_id": request_id,
                "resilience_enabled": True
            }
        )
    
    finally:
        # Limpiar contexto
        clear_request_context()

# =============================================================================
# IMPORTACIÓN Y REGISTRO DE ROUTERS
# =============================================================================

# Routers principales
app.include_router(auth_router)
app.include_router(stats_router)
app.include_router(products_router)
app.include_router(whatsapp_router)
app.include_router(webhooks_router)
app.include_router(leads_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(agents_router)
app.include_router(payments_router)
app.include_router(ingest_router)
app.include_router(voice_router)
app.include_router(channels_router)
app.include_router(whatsapp_health_router)
app.include_router(whatsapp_cloud_router)
app.include_router(quota_router)
app.include_router(oauth_sync_router)
app.include_router(sync_router)
app.include_router(upload_router)
app.include_router(sales_router, prefix="/api/v1")
app.include_router(analytics_router)
app.include_router(billing_router)
app.include_router(plans_router)

# Router de resiliencia (último para prioridad)
app.include_router(resilience_router)

# =============================================================================
# ENDPOINTS DE OBSERVABILIDAD CON RESILIENCIA
# =============================================================================

@app.get("/", tags=["Sistema"])
async def root():
    """Endpoint raíz con información de resiliencia"""
    structured_logger = get_logger("root")
    structured_logger.info("root", "Request al endpoint raíz")
    
    return {
        "servicio": config.app_nombre,
        "version": config.app_version,
        "estado": "operativo",
        "entorno": config.app_env,
        "resilience": {
            "enabled": True,
            "features": [
                "bulkhead_pattern",
                "circuit_breakers", 
                "timeouts",
                "retries",
                "rate_limiting"
            ]
        },
        "observabilidad": {
            "metrics": "/metrics",
            "health": "/health",
            "resilience": "/api/v1/resilience/status",
            "tracing": "enabled" if get_tracing_manager().enabled else "disabled"
        },
        "docs": "/docs",
    }

@app.get("/health", tags=["Sistema"])
async def health_check():
    """Health check completo con resiliencia"""
    structured_logger = get_logger("health")
    tracing = get_tracing_manager()
    
    with tracing.trace_async_function("health_check") as span:
        span.set_tag("service", "fluxagent")
        
        estado_servicios = {
            "postgres": "desconocido",
            "redis": "desconocido",
            "ollama": "desconocido",
            "cache": "desconocido",
            "resilience": "desconocido",
            "metrics": "desconocido"
        }
        
        # Verificar PostgreSQL
        try:
            from database import engine
            from sqlalchemy import text
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            estado_servicios["postgres"] = "ok"
            span.set_tag("postgres.status", "ok")
        except Exception:
            estado_servicios["postgres"] = "error"
            span.set_tag("postgres.status", "error")
        
        # Verificar Redis
        try:
            from core.cache.client import get_cache_client
            cache = get_cache_client()
            if await cache.health_check():
                estado_servicios["redis"] = "ok"
                span.set_tag("redis.status", "ok")
            else:
                estado_servicios["redis"] = "error"
                span.set_tag("redis.status", "error")
        except Exception:
            estado_servicios["redis"] = "error"
            span.set_tag("redis.status", "error")
        
        # Verificar Ollama
        try:
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(f"{config.ollama_base_url}/api/tags")
                if resp.status_code == 200:
                    estado_servicios["ollama"] = "ok"
                    span.set_tag("ollama.status", "ok")
                else:
                    estado_servicios["ollama"] = "error"
                    span.set_tag("ollama.status", "error")
        except Exception:
            estado_servicios["ollama"] = "error"
            span.set_tag("ollama.status", "error")
        
        # Verificar cache
        try:
            from core.cache.client import get_cache_client
            cache = get_cache_client()
            stats = cache.get_stats()
            estado_servicios["cache"] = "ok"
            span.set_tag("cache.status", "ok")
            span.set_tag("cache.hit_ratio", stats.hit_rate)
        except Exception:
            estado_servicios["cache"] = "error"
            span.set_tag("cache.status", "error")
        
        # Verificar resiliencia
        try:
            from services.resilient_services import get_resilience_status
            resilience_status = await get_resilience_status()
            estado_servicios["resilience"] = "ok"
            span.set_tag("resilience.status", "ok")
        except Exception:
            estado_servicios["resilience"] = "error"
            span.set_tag("resilience.status", "error")
        
        # Verificar métricas
        try:
            from prometheus_client import CONTENT_TYPE_LATEST
            estado_servicios["metrics"] = "ok"
            span.set_tag("metrics.status", "ok")
        except Exception:
            estado_servicios["metrics"] = "error"
            span.set_tag("metrics.status", "error")
        
        # Log de health check
        structured_logger.info("health", "Health check completado", metadata=estado_servicios)
        
        # Métricas de health check
        metrics = get_metrics()
        for service, status in estado_servicios.items():
            metrics.set_connection_count(
                count=1 if status == "ok" else 0,
                connection_type=service,
                tenant_id="system"
            )
        
        return {
            "status": "healthy" if all(s == "ok" for s in estado_servicios.values()) else "degraded",
            "timestamp": time.time(),
            "services": estado_servicios,
            "version": config.app_version,
            "resilience": {
                "enabled": True,
                "status": estado_servicios["resilience"]
            },
            "observabilidad": {
                "tracing": tracing.enabled,
                "cache": "enabled",
                "rate_limiting": "enabled"
            }
        }

@app.get("/metrics", tags=["Observabilidad"])
async def metrics_endpoint():
    """Endpoint de métricas Prometheus con resiliencia"""
    structured_logger = get_logger("metrics")
    
    try:
        metrics = get_metrics()
        structured_logger.info("metrics", "Endpoint de métricas consultado")
        return metrics.get_metrics()
    except Exception as e:
        structured_logger.error("metrics", "Error obteniendo métricas", error=e)
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=500,
            content={"error": "Error obteniendo métricas"}
        )

# =============================================================================
# EJECUCIÓN
# =============================================================================

if __name__ == "__main__":
    structured_logger = get_logger("main")
    structured_logger.info("main", "Iniciando FluxAgent V2 con resiliencia avanzada")
    
    uvicorn.run(
        "main_resilience:app",
        host="0.0.0.0",
        port=8000,
        reload=config.es_desarrollo,
        log_config=None,  # Usar logging estructurado personalizado
        access_log=False,  # Deshabilitar access log por defecto
    )
