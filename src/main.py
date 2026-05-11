# =============================================================================
# FLUXAGENT V2 — ENTRY POINT PRINCIPAL
# =============================================================================

import logging
import time
from contextlib import asynccontextmanager
from typing import Optional
from uuid import UUID

import uvicorn
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy.ext.asyncio import AsyncSession

from config import obtener_config
from database import cerrar_db, configurar_rls, inicializar_db, obtener_sesion
from auth import get_tenant_actual, get_tenant_actual_opcional, get_usuario_actual
from core.plan_manager import PlanManager
from routers.auth_router import router as auth_router
# from routers.stats_router import router as stats_router  # Legacy - reemplazado por analytics_router
from routers.catalog_router import router as catalog_router
from routers.whatsapp_router import router as whatsapp_router
from routers.webhooks_router import router as webhooks_router
from routers.leads_router import router as leads_router
from routers.admin_router import router as admin_router
from routers.users_router import router as users_router
from routers.agents_router import router as agents_router
from routers.payments_router import router as payments_router
from routers.ingest_router import router as ingest_router, ws_router
from routers.voice_router import router as voice_router
from routers.channels_router import router as channels_router
from routers.whatsapp_health_router import router as whatsapp_health_router
from routers.health_router import router as health_router
from routers.whatsapp_cloud_router import router as whatsapp_cloud_router
from routers.quota_router import router as quota_router
from routers.oauth_sync_router import router as oauth_sync_router
from routers.sync_router import router as sync_router
from routers.upload_router import router as upload_router
from app.routers.sales_agent_router import router as sales_router
from routers.analytics_router import router as analytics_router
from routers.billing_router import router as billing_router
from routers.plans_router import router as plans_router
from routers.handoff_router import router as handoff_router
from routers.ws_gateway_router import router as ws_gateway_router
from routers.insights_router import router as insights_router
from routers.explain_router import router as explain_router
from routers.yanua_router import router as yanua_router
from routers.commerce_router import router as commerce_router
from routers.checkout_router import router as checkout_router
from routers.onboarding_router import router as onboarding_router
from routers.timeline_router import router as timeline_router
from routers.capabilities_router import router as capabilities_router
from routers.playbooks_router import router as playbooks_router
from routers.health_router import router as health_router
from routers.event_actions_router import router as event_actions_router
from routers.connectors_router import router as connectors_router
from routers.ai_copilot_router import router as ai_copilot_router
# Nota: chat_router no tiene un APIRouter registrado, provee la función lógica a webhooks

from core.metrics import start_metrics_server
from tasks.rag_scheduler import start_scheduler as start_rag_scheduler, stop_scheduler as stop_rag_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)
config = obtener_config()


# =============================================================================
# CICLO DE VIDA
# =============================================================================
from core.dependencies import get_redis
from core.event_bus import EventBus
from core.ws_event_bridge import WSRealtimeBridge
from core.realtime_gateway import RealtimeGateway
from services.lead_scorer import LeadScorer
from services.tool_executor import ToolExecutor
from services.tools.crm_tools import TOOL_UPDATE_LEAD
from services.ai_memory import AIMemoryManager
from services.policy_engine import PolicyEngine
from services.ai_orchestrator import AIOrchestrator
from domain.events import EventType
from core.event_bus import EventBus
from services.usage_tracker import UsageTracker
from services.quota_manager import QuotaManager
from routers.usage_router import router as usage_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Iniciando {config.app_nombre} v{config.app_version} [{config.app_env}]")

    # Inicializar servicio de cifrado (antes de cualquier operación con BD)
    try:
        from core.encryption import EncryptionService
        EncryptionService.initialize()
    except Exception as e:
        logger.warning(f"⚠️  EncryptionService no iniciado: {e}")

    await inicializar_db()

    # Inicializar Redis, Gateway y Event Bus
    redis_conn = await get_redis()
    
    # Nuevo Gateway Unificado de Tiempo Real
    realtime_gateway = RealtimeGateway(redis_conn)
    app.state.realtime_gateway = realtime_gateway
    
    event_bus = EventBus(redis_conn)
    ws_bridge = WSRealtimeBridge(realtime_gateway)
    ws_bridge.register(event_bus)
    app.state.event_bus = event_bus

    # Motor de Scoring
    lead_scorer = LeadScorer(redis_conn, event_bus)
    lead_scorer.register()
    app.state.lead_scorer = lead_scorer
    
    # Motor de Herramientas
    tool_executor = ToolExecutor() 
    from core.tool_registry import COMMERCE_TOOLS
    for tool in COMMERCE_TOOLS:
        tool_executor.register(tool)
    app.state.tool_executor = tool_executor

    # === NUEVO: AI Orchestrator + Policy Engine ===
    memory_manager = AIMemoryManager(redis=redis_conn, db_session=None)
    policy_engine = PolicyEngine(redis=redis_conn, db=None)
    
    orchestrator = AIOrchestrator(
        redis=redis_conn,
        event_bus=event_bus,
        policy_engine=policy_engine,
        tool_executor=tool_executor,
        memory_manager=memory_manager,
        llm_provider=None, # Inyectar provider real más adelante
    )
    
    # Suscribirse a eventos de entrada
    import asyncio
    asyncio.create_task(
        event_bus.subscribe(
            event_types=[EventType.MESSAGE_RECEIVED, EventType.VOICE_TRANSCRIPTION_CHUNK],
            handler=orchestrator.process_event,
            consumer_name="ai-orchestrator",
        )
    )
    
    # Guardar en app state para inyección en routers
    app.state.memory_manager = memory_manager
    app.state.orchestrator = orchestrator
    app.state.policy_engine = policy_engine

    # === NUEVO: Token Economy Engine ===
    usage_tracker = UsageTracker(redis=redis_conn, db_session_factory=None) # db_session_factory inyectable
    quota_manager = QuotaManager(redis=redis_conn, db_session_factory=None)

    await usage_tracker.start()

    app.state.usage_tracker = usage_tracker
    app.state.quota_manager = quota_manager
    
    # Manejar Kill Switch
    from services.billing_alert_service import BillingAlertService
    billing_alert = BillingAlertService(event_bus, redis_conn, None)
    app.state.billing_alert = billing_alert

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(config.redis_url, decode_responses=True)
        await r.ping()
        await r.aclose()
        logger.info("✅ Redis disponible")
    except Exception as exc:
        logger.warning(f"⚠️  Redis no disponible: {exc}")

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{config.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                modelos = [m.get("name") for m in resp.json().get("models", [])]
                logger.info(f"✅ Ollama disponible. Modelos: {modelos}")
    except Exception as exc:
        logger.warning(f"⚠️  Ollama no respondió: {exc}")

    logger.info("✅ FluxAgent V2 listo")
    
    # Iniciar servidor de métricas Prometheus
    try:
        start_metrics_server(8001)
        logger.info("📊 Métricas Prometheus disponibles en http://localhost:8001/metrics")
    except Exception as e:
        logger.warning(f"⚠️  Servidor métricas no iniciado: {e}")

    # Iniciar scheduler de reset de cuotas (02:00 UTC diario)
    try:
        from tasks.quota_reset import start_quota_scheduler
        await start_quota_scheduler()
    except Exception as e:
        logger.warning(f"⚠️  Quota scheduler no iniciado: {e}")
        
    # Iniciar scheduler de RAG Sync (Sheets/Excel)
    try:
        from tasks.rag_scheduler import scheduler
        start_rag_scheduler()
        
        # Inyectar el scheduler global al gestor de followups
        from tasks.followups import set_followup_scheduler
        set_followup_scheduler(scheduler)
        
    except Exception as e:
        logger.warning(f"⚠️  RAG Sync scheduler no iniciado: {e}")
        
    # Inicializar handlers del event_bus (Payment Followups, etc)
    try:
        # EventBus is globally imported
        from domain.events import DomainEvent
        from tasks.followups import schedule_followup
        
        # Función para registrar los handlers
        async def handle_payment_completed(event: DomainEvent):
            customer_phone = event.payload.dict().get("customer_phone") or "desconocido"
            order_id = event.payload.dict().get("order_id")
            # Programar survey a las 72h
            schedule_followup(customer_phone, "post_purchase_survey", {"order_id": order_id}, delay_hours=72)
            # Programar confirmación inmediata
            schedule_followup(customer_phone, "order_confirmation", {"order_id": order_id}, delay_minutes=1)
            
        async def handle_payment_failed(event: DomainEvent):
            customer_phone = event.payload.dict().get("customer_phone") or "desconocido"
            order_id = event.payload.dict().get("order_id")
            schedule_followup(customer_phone, "payment_pending", {"order_id": order_id}, delay_minutes=5)
            
        await event_bus.subscribe([EventType.PAYMENT_COMPLETED], handle_payment_completed, "followups_worker")
        await event_bus.subscribe([EventType.PAYMENT_FAILED], handle_payment_failed, "followups_worker")
        
        from core.event_listeners import persist_event_to_timeline
        from database import obtener_sesion
        
        async def timeline_wrapper(event):
            from database import SessionLocal
            async with SessionLocal() as db:
                await persist_event_to_timeline(event, db, redis_conn)
                
        # Suscribir a los eventos que queremos en el timeline unificado
        timeline_events = [
            EventType.MESSAGE_RECEIVED, EventType.MESSAGE_SENT,
            EventType.QUOTE_GENERATED, EventType.QUOTE_ACCEPTED,
            EventType.ORDER_CREATED, EventType.PAYMENT_COMPLETED,
            EventType.PAYMENT_FAILED, EventType.BOOKING_CONFIRMED,
            EventType.HANDOFF_REQUESTED, EventType.FOLLOWUP_SCHEDULED
        ]
        await event_bus.subscribe(timeline_events, timeline_wrapper, "timeline_worker")
        
        logger.info("✅ EventBus handlers para followups registrados.")
    except Exception as e:
        logger.warning(f"⚠️ Error registrando handlers de EventBus: {e}")
    
    yield
    logger.info("🛑 Cerrando FluxAgent V2...")
    
    # Detener scheduler antes de cerrar
    try:
        from tasks.quota_reset import stop_quota_scheduler
        await stop_quota_scheduler()
    except Exception:
        pass
        
    try:
        stop_rag_scheduler()
    except Exception:
        pass
    
    # Shutdown seguro de Event Bus y Usage Tracker
    if hasattr(app.state, "usage_tracker"):
        await app.state.usage_tracker.stop()
        
    if hasattr(app.state, "event_bus"):
        await app.state.event_bus.close()
        
    await cerrar_db()


# =============================================================================
# INSTANCIA FASTAPI
# =============================================================================

from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title=config.app_nombre,
    version=config.app_version,
    description="Motor de Agentes IA Multi-tenant con RAG y Streaming",
    docs_url="/docs" if not config.es_produccion else None,
    redoc_url="/redoc" if not config.es_produccion else None,
    lifespan=lifespan,
)

import os
os.makedirs("uploads/avatars", exist_ok=True)
os.makedirs("uploads/knowledge", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "X-Correlation-ID"],
)

# Correlation middleware: auto-propagates X-Correlation-ID en todos los requests
from core.correlation import CorrelationMiddleware
app.add_middleware(CorrelationMiddleware)


from core.middleware.tenant_isolation import setup_middlewares

# Configurar middlewares personalizados
setup_middlewares(app)


# =============================================================================
# ROUTERS
# =============================================================================

app.include_router(auth_router)
from routers.usage_router import router as usage_router
app.include_router(usage_router)
# app.include_router(stats_router)  # Legacy - reemplazado por analytics_router
app.include_router(catalog_router)
app.include_router(whatsapp_router)
app.include_router(webhooks_router)
app.include_router(leads_router)
app.include_router(admin_router)
app.include_router(users_router)
app.include_router(agents_router)
app.include_router(payments_router)
app.include_router(ingest_router)
app.include_router(ws_router)
app.include_router(voice_router)
app.include_router(channels_router)
app.include_router(whatsapp_health_router)
app.include_router(health_router)
app.include_router(whatsapp_cloud_router)
app.include_router(quota_router)
app.include_router(oauth_sync_router)
app.include_router(sync_router)
app.include_router(upload_router)
app.include_router(sales_router, prefix="/api/v1")
app.include_router(analytics_router)
app.include_router(billing_router)
app.include_router(plans_router)
app.include_router(ws_gateway_router)
app.include_router(handoff_router)
app.include_router(insights_router, prefix="/api/v1")
app.include_router(explain_router, prefix="/api/v1")
app.include_router(yanua_router, prefix="/api/v1")
app.include_router(commerce_router)
app.include_router(checkout_router)
app.include_router(onboarding_router)
app.include_router(timeline_router)
app.include_router(capabilities_router)
app.include_router(playbooks_router)
app.include_router(health_router)
app.include_router(event_actions_router)
app.include_router(connectors_router)
app.include_router(ai_copilot_router)

# =============================================================================
# HANDLERS DE EXCEPCIONES ESPECÍFICOS
# =============================================================================
# Manejo granular de errores según tipo y contexto
# Mejor experiencia para desarrolladores y usuarios
# =============================================================================

from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import DBAPIError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
# from auth import TenantNotFoundError, AuthenticationError

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Maneja errores HTTP 4xx conocidos"""
    logger.warning(f"HTTP {exc.status_code} en {request.url}: {exc.detail}")
    
    # Mapear códigos a mensajes amigables
    error_messages = {
        400: "Solicitud inválida",
        401: "No autorizado",
        403: "Acceso denegado",
        404: "Recurso no encontrado",
        405: "Método no permitido",
        429: "Demasiadas solicitudes"
    }
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "http_error",
            "codigo": exc.status_code,
            "mensaje": error_messages.get(exc.status_code, exc.detail),
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Maneja errores de validación Pydantic"""
    logger.warning(f"Validación fallida en {request.url}: {exc.errors()}")
    
    # Formatear errores para mejor UX
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(x) for x in error["loc"])
        formatted_errors.append({
            "campo": field,
            "mensaje": error["msg"],
            "valor": error.get("input")
        })
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "validacion_fallida",
            "mensaje": "Datos de entrada inválidos",
            "detalles": formatted_errors,
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(IntegrityError)
async def db_integrity_handler(request: Request, exc: IntegrityError):
    """Maneja errores de integridad de DB (unique constraints, FK, etc)"""
    logger.error(f"Error de integridad DB: {exc.orig}")
    
    # Detectar tipo específico de error
    error_msg = str(exc.orig).lower()
    
    if "unique" in error_msg:
        detalle = "El recurso ya existe"
        codigo = "recurso_duplicado"
    elif "foreign key" in error_msg:
        detalle = "Referencia inválida a otro recurso"
        codigo = "referencia_invalida"
    elif "not null" in error_msg:
        detalle = "Campo requerido faltante"
        codigo = "campo_requerido"
    else:
        detalle = "Conflicto de datos"
        codigo = "conflicto_datos"
    
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": codigo,
            "mensaje": detalle,
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

@app.exception_handler(DBAPIError)
async def db_error_handler(request: Request, exc: DBAPIError):
    """Maneja errores genéricos de base de datos"""
    logger.error(f"Error de base de datos: {exc.orig}", exc_info=True)
    
    # En producción, no exponer detalles de DB
    if config.es_desarrollo:
        detalle = str(exc.orig)
    else:
        detalle = "Error en el servicio de base de datos"
    
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": "error_db",
            "mensaje": detalle,
            "path": str(request.url.path),
            "timestamp": time.time()
        }
    )

# @app.exception_handler(TenantNotFoundError)
# async def tenant_not_found_handler(request: Request, exc: TenantNotFoundError):
#     """Maneja errores de tenant no encontrado"""
#     logger.warning(f"Tenant no encontrado: {exc}")
#     return JSONResponse(
#         status_code=status.HTTP_404_NOT_FOUND,
#         content={
#             "error": "tenant_no_encontrado",
#             "mensaje": "Tenant no encontrado",
#             "path": str(request.url.path),
#             "timestamp": time.time()
#         }
#     )

# @app.exception_handler(AuthenticationError)
# async def auth_error_handler(request: Request, exc: AuthenticationError):
#     """Maneja errores de autenticación"""
#     logger.warning(f"Error de autenticación: {exc}")
#     return JSONResponse(
#         status_code=status.HTTP_401_UNAUTHORIZED,
#         content={
#             "error": "autenticacion_fallida",
#             "mensaje": "Credenciales inválidas o expiradas",
#             "path": str(request.url.path),
#             "timestamp": time.time()
#         }
#     )

# Mantener handler genérico SOLO para logging y fallback
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Último recurso: loguear pero no exponer detalles"""
    logger.critical(
        f"ERROR NO MANEJADO en {request.method} {request.url}: "
        f"{type(exc).__name__}: {exc}",
        exc_info=True
    )
    
    # En producción: enviar alerta a Sentry/PagerDuty aquí
    if not config.es_desarrollo:
        # TODO: Integrar con sistema de alertas
        pass
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "error_interno",
            "mensaje": "Ocurrió un error inesperado",
            "path": str(request.url.path),
            "timestamp": time.time(),
            "request_id": getattr(request.state, 'request_id', None)
        }
    )


def limiter_get_remote_address(request: Request):
    """Limiter custom que considera X-Forwarded-For para proxies."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return get_remote_address(request)


# =============================================================================
# RUTAS BASE
# =============================================================================

@app.get("/", tags=["Sistema"])
async def raiz():
    return {
        "servicio": config.app_nombre,
        "version":  config.app_version,
        "estado":   "operativo",
        "entorno":  config.app_env,
        "docs":     "/docs",
    }


@app.get("/health", tags=["Sistema"])
async def health_check():
    """Verifica el estado de PostgreSQL, Redis y Ollama."""
    estado_servicios = {"postgres": "desconocido", "redis": "desconocido", "ollama": "desconocido"}

    try:
        from database import engine
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        estado_servicios["postgres"] = "ok"
    except Exception:
        estado_servicios["postgres"] = "error"

    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(config.redis_url)
        await r.ping()
        await r.aclose()
        estado_servicios["redis"] = "ok"
    except Exception:
        estado_servicios["redis"] = "error"

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{config.ollama_base_url}/api/tags")
            estado_servicios["ollama"] = "ok" if resp.status_code == 200 else "error"
    except Exception:
        estado_servicios["ollama"] = "error"

    # Solo Postgres y Redis son críticos para el estado 200/503
    criticos_ok = estado_servicios["postgres"] == "ok" and estado_servicios["redis"] == "ok"
    hay_error_en_alguno = any(v == "error" for v in estado_servicios.values())
    
    return JSONResponse(
        status_code=200 if criticos_ok else 503,
        content={
            "estado": "saludable" if not hay_error_en_alguno else ("degradado" if criticos_ok else "fuera_de_servicio"),
            "servicios": estado_servicios,
            "version": config.app_version,
        },
    )


# =============================================================================
# ENDPOINT: GET /api/v1/knowledge
# =============================================================================

@app.get(
    "/api/v1/knowledge",
    tags=["Conocimiento RAG"],
    summary="Lista los documentos indexados del tenant autenticado",
)
async def listar_conocimiento(
    limit: int = 100,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Retorna los chunks de conocimiento del tenant actual con estadísticas por fuente."""
    from sqlalchemy import text
    await configurar_rls(db, tenant_id)
    result = await db.execute(
        text("""
            SELECT fuente_nombre, fuente_tipo, COUNT(*) as chunks, MAX(creado_en) as ultima_ingesta
            FROM knowledge_chunks
            WHERE tenant_id = :tid
            GROUP BY fuente_nombre, fuente_tipo
            ORDER BY ultima_ingesta DESC
            LIMIT :limit
        """),
        {"tid": str(tenant_id), "limit": limit},
    )
    fuentes = [
        {
            "fuente_nombre":   row.fuente_nombre,
            "fuente_tipo":     row.fuente_tipo,
            "chunks":          row.chunks,
            "ultima_ingesta":  str(row.ultima_ingesta),
        }
        for row in result.fetchall()
    ]
    # Total de chunks
    total_result = await db.execute(
        text("SELECT COUNT(*) FROM knowledge_chunks WHERE tenant_id = :tid"),
        {"tid": str(tenant_id)},
    )
    total = total_result.scalar() or 0
    return {"total_chunks": total, "fuentes": fuentes, "tenant_id": str(tenant_id)}


# =============================================================================
# ENDPOINT: DELETE /api/v1/knowledge/{fuente_nombre}
# =============================================================================

@app.delete(
    "/api/v1/knowledge/{fuente_nombre}",
    tags=["Conocimiento RAG"],
    summary="Elimina todos los chunks de un documento por su nombre",
)
async def eliminar_fuente(
    fuente_nombre: str,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Elimina todos los vectores de una fuente específica del tenant actual."""
    from sqlalchemy import text
    await configurar_rls(db, tenant_id)
    result = await db.execute(
        text("""
            DELETE FROM knowledge_chunks
            WHERE tenant_id = :tid AND fuente_nombre = :nombre
        """),
        {"tid": str(tenant_id), "nombre": fuente_nombre},
    )
    await db.commit()
    return {"eliminados": result.rowcount, "fuente": fuente_nombre}


@app.delete(
    "/api/v1/knowledge",
    tags=["Conocimiento RAG"],
    summary="Vacía todo el conocimiento (chunks y productos)",
)
async def vaciar_cerebro(
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Elimina todos los datos de RAG e inventario del tenant actual."""
    from sqlalchemy import text
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No autenticado")

    await configurar_rls(db, tenant_id)
    
    # Vaciar vectores
    res_chunks = await db.execute(
        text("DELETE FROM knowledge_chunks WHERE tenant_id = :tid"),
        {"tid": str(tenant_id)}
    )
    # Vaciar productos estructurados
    res_prods = await db.execute(
        text("DELETE FROM productos WHERE tenant_id = :tid"),
        {"tid": str(tenant_id)}
    )
    await db.commit()
    
    return {
        "mensaje": "Cerebro y catálogo vaciados correctamente.",
        "chunks_eliminados": res_chunks.rowcount,
        "productos_eliminados": res_prods.rowcount
    }


# Las rutas de ingesta asíncrona han sido movidas a routers/ingest_router.py

# =============================================================================
# ENDPOINT: GET /api/v1/knowledge/{fuente_nombre}/chunks
# =============================================================================
from sqlalchemy import text
@app.get(
    "/api/v1/knowledge/{fuente_nombre}/chunks",
    tags=["Conocimiento"],
    summary="Obtiene los fragmentos extraídos de una fuente",
)
async def obtener_chunks_fuente(
    fuente_nombre: str,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    await configurar_rls(db, tenant_id)
    # decode en caso de que venga encodeada
    import urllib.parse
    fuente_decodificada = urllib.parse.unquote(fuente_nombre)
    
    res = await db.execute(
        text("""
            SELECT id, contenido, orden_chunk, fuente_tipo 
            FROM knowledge_chunks 
            WHERE tenant_id = :tid AND fuente_nombre = :fuente
            ORDER BY orden_chunk ASC
        """),
        {"tid": str(tenant_id), "fuente": fuente_decodificada}
    )
    chunks = res.fetchall()
    return {
        "fuente": fuente_decodificada,
        "total_chunks": len(chunks),
        "chunks": [{"id": str(c.id), "contenido": c.contenido, "orden": c.orden_chunk, "tipo": c.fuente_tipo} for c in chunks]
    }

# =============================================================================
# SCHEMAS DE CHAT
# =============================================================================

class MensajeChatSchema(BaseModel):
    rol:       str   # 'usuario' | 'asistente'
    contenido: str


class SolicitudChat(BaseModel):
    tenant_id:   Optional[UUID] = None # Se obtiene del JWT si no se envía
    agent_id:    Optional[UUID] = None
    session_id:  str
    mensaje:     str
    historial:   list[MensajeChatSchema] = []
    # Configuración del agente (se puede sobreescribir desde la DB en versiones futuras)
    configuracion: dict = {
        "nombre":       "Asistente",
        "genero":       "femenino",
        "humor":        "profesional",
        "personalidad": "Soy un asistente de ventas eficiente.",
        "tipo_negocio": "Empresa de servicios",
        "instrucciones": "Ayuda al cliente a encontrar lo que necesita.",
        "modelo":       "qwen2.5:3b",
        "temperatura":  0.7,
        "max_tokens":   512,
    }

    model_config = {"json_schema_extra": {
        "example": {
            "tenant_id":  "11111111-1111-1111-1111-111111111111",
            "session_id": "sesion-abc-123",
            "mensaje":    "¿Qué productos tienen disponibles?",
            "historial":  [],
            "configuracion": {"nombre": "Luna", "humor": "amigable", "modelo": "qwen2.5:3b"},
        }
    }}


# =============================================================================
# ENDPOINT: POST /api/v1/chat
# =============================================================================

@app.post(
    "/api/v1/chat",
    tags=["Chat"],
    summary="Conversación completa con el agente (respuesta única)",
)
async def chat_completo(
    solicitud: SolicitudChat,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db:        AsyncSession = Depends(obtener_sesion),
):
    """
    Envia un mensaje al agente y recibe la respuesta completa.

    Flujo:
      1. Busca contexto relevante en pgvector (RAG)
      2. Genera respuesta con Ollama
      3. Retorna la respuesta completa

    Ideal para: WhatsApp, Telegram, integraciones que no soportan streaming.
    """
    from agents.base_agent import ContextoAgente, MensajeChat
    from agents.sales_agent import AgentDeVentas
    from sqlalchemy import text
    import random

    # Prioridad: 1. Token JWT, 2. Body (si es demo)
    tid = tenant_id or solicitud.tenant_id
    if not tid:
        raise HTTPException(status_code=401, detail="tenant_id requerido")

    await configurar_rls(db, tid)

    contexto = ContextoAgente(
        tenant_id=tid,
        agent_id=solicitud.agent_id,
        session_id=solicitud.session_id,
        mensaje_usuario=solicitud.mensaje,
        historial=[MensajeChat(rol=m.rol, contenido=m.contenido) for m in solicitud.historial],
        configuracion=solicitud.configuracion,
    )

    agente = AgentDeVentas()
    try:
        respuesta = await agente.procesar(contexto, sesion=db)
        
        # Registrar en analíticas (Dashboard)
        try:
            sentimiento = random.uniform(0.2, 1.0) # Simulación positiva para dashboard
            await db.execute(text("""
                INSERT INTO conversaciones 
                (tenant_id, agent_id, lead_externo_id, canal, tokens_salida, estado, sentimiento)
                VALUES (:tid, :aid, :session, 'web_chat', :tokens, 'activa', :sentimiento)
            """), {
                "tid": str(tid),
                "aid": str(solicitud.agent_id) if solicitud.agent_id else None,
                "session": solicitud.session_id,
                "tokens": respuesta.tokens_usados,
                "sentimiento": sentimiento
            })
            await db.commit()
        except Exception as e:
            logger.warning(f"No se pudo registrar metrica de conversacion: {e}")

        return {
            "session_id":   solicitud.session_id,
            "respuesta":    respuesta.contenido,
            "tokens":       respuesta.tokens_usados,
            "modelo":       respuesta.modelo_usado,
            "fuentes_rag":  respuesta.fuentes_rag,
            "chunks_usados": respuesta.metadatos.get("chunks_usados", 0),
        }
    finally:
        await agente.cerrar()


# =============================================================================
# ENDPOINT: POST /api/v1/chat/stream
# =============================================================================

@app.post(
    "/api/v1/chat/stream",
    tags=["Chat"],
    summary="Conversación con streaming SSE (token a token)",
    response_class=StreamingResponse,
    dependencies=[Depends(PlanManager.verificar_limite_diario("messages"))]
)
async def chat_stream(
    solicitud: SolicitudChat,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db:        AsyncSession = Depends(obtener_sesion),
):
    """
    Envía un mensaje al agente y recibe la respuesta en tiempo real (Server-Sent Events).

    Protocolo SSE:
      - Cada token se emite como: `data: {"token": "...", "done": false}\\n\\n`
      - Al terminar:              `data: {"token": "", "done": true, "modelo": "..."}\\n\\n`
      - Si hay error:             `data: {"error": "...", "done": true}\\n\\n`

    Ideal para: Web Chat, aplicaciones React/Next.js con EventSource.

    **Ejemplo con JavaScript:**
    ```js
    const es = new EventSource('/api/v1/chat/stream');
    es.onmessage = (e) => {
      const {token, done} = JSON.parse(e.data);
      if (done) es.close();
      else mostrar(token);
    };
    ```
    """
    from agents.base_agent import ContextoAgente, MensajeChat
    from agents.sales_agent import AgentDeVentas

    # Prioridad: 1. Token JWT, 2. Body (si es demo)
    tid = tenant_id or solicitud.tenant_id
    if not tid:
        raise HTTPException(status_code=401, detail="tenant_id requerido")

    await configurar_rls(db, tid)

    contexto = ContextoAgente(
        tenant_id=tid,
        agent_id=solicitud.agent_id,
        session_id=solicitud.session_id,
        mensaje_usuario=solicitud.mensaje,
        historial=[MensajeChat(rol=m.rol, contenido=m.contenido) for m in solicitud.historial],
        configuracion=solicitud.configuracion,
    )

    agente = AgentDeVentas()

    async def generador_sse():
        try:
            async for token_sse in agente.procesar_streaming(contexto, sesion=db):
                yield token_sse
        finally:
            await agente.cerrar()
            PlanManager.registrar_uso(str(tid), "messages", 1)

    return StreamingResponse(
        generador_sse(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "X-Accel-Buffering": "no",   # Desactivar buffering en Nginx/Traefik
            "Connection":       "keep-alive",
        },
    )


# =============================================================================
# ENDPOINT: POST /api/v1/whatsapp/webhook
# =============================================================================

from fastapi import BackgroundTasks
import httpx

async def procesar_mensaje_whatsapp(tenant_id: UUID, session_id: str, mensaje: str, instance_name: str, remote_jid: str):
    from agents.base_agent import ContextoAgente
    from agents.sales_agent import AgentDeVentas
    from database import SesionLocal, configurar_rls

    logger.info(f"[WA] Procesando mensaje | jid={remote_jid} | msg='{mensaje[:60]}'")

    # 1. Typing indicator
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(
                f"{config.evolution_api_url}/chat/sendPresence/{instance_name}",
                headers={"apikey": config.evolution_api_key},
                json={"number": remote_jid, "presence": "composing", "delay": 8000},
            )
            logger.info("[WA] Typing indicator enviado")
    except Exception as e:
        logger.warning(f"[WA] No se pudo enviar typing: {e}")

    # 2. Procesar con IA usando sesión limpia
    texto_respuesta = "Lo siento, tuve un problema técnico. ¿Puedes repetir tu consulta?"
    try:
        async with SesionLocal() as db:
            await configurar_rls(db, tenant_id)

            # Obtener el agente (usamos el primero encontrado si no hay ID específico)
            res_agent = await db.execute(text("""
                SELECT nombre, humor, personalidad, genero, tipo_negocio, instrucciones, modelo, temperatura, max_tokens, script_ventas
                FROM agents WHERE tenant_id = :tid LIMIT 1
            """), {"tid": str(tenant_id)})
            agente_db = res_agent.fetchone()

            if agente_db:
                config_agente = {
                    "nombre": agente_db.nombre,
                    "humor": agente_db.humor,
                    "personalidad": agente_db.personalidad,
                    "genero": agente_db.genero,
                    "tipo_negocio": agente_db.tipo_negocio,
                    "instrucciones": agente_db.instrucciones,
                    "modelo": agente_db.modelo,
                    "temperatura": agente_db.temperatura,
                    "max_tokens": agente_db.max_tokens,
                    "script_ventas": agente_db.script_ventas
                }
            else:
                config_agente = {
                    "nombre": "FluxBot",
                    "humor": "profesional",
                    "modelo": "qwen2.5:3b",
                    "temperatura": 0.7,
                    "max_tokens": 512,
                }

            contexto = ContextoAgente(
                tenant_id=tenant_id,
                agent_id=None,
                session_id=session_id,
                mensaje_usuario=mensaje,
                configuracion=config_agente,
            )

            agente = AgentDeVentas()
            try:
                respuesta_ai = await agente.procesar(contexto, sesion=db)
                texto_respuesta = respuesta_ai.contenido
                logger.info(f"[WA] Respuesta generada ({len(texto_respuesta)} chars)")
            except Exception as exc:
                logger.error(f"[WA] Error en agente IA: {exc}", exc_info=True)
            finally:
                await agente.cerrar()

            await db.commit()

    except Exception as exc:
        logger.error(f"[WA] Error crítico en sesión DB: {exc}", exc_info=True)

    # 3. Enviar respuesta a WhatsApp
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{config.evolution_api_url}/message/sendText/{instance_name}",
                headers={"apikey": config.evolution_api_key},
                json={
                    "number": remote_jid,
                    "text": texto_respuesta,
                    "delay": 1000,
                },
            )
            logger.info(f"[WA] Mensaje enviado | status={resp.status_code}")
    except Exception as e:
        logger.error(f"[WA] Error enviando respuesta a Evolution: {e}", exc_info=True)

@app.post(
    "/api/v1/whatsapp/webhook",
    tags=["WhatsApp"],
    summary="Recibe mensajes desde Evolution API",
)
async def whatsapp_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    payload = await request.json()
    
    # Validar evento de mensaje
    if payload.get("event") != "messages.upsert":
        return {"status": "ignored", "reason": "not a message event"}

    data = payload.get("data", {})
    message = data.get("message", {})
    key = data.get("key", {})

    # Ignorar mensajes propios o del sistema
    if key.get("fromMe") or not message:
        return {"status": "ignored", "reason": "fromMe or empty message"}

    instance_name = payload.get("instance")
    remote_jid = key.get("remoteJid")
    
    # Extraer texto del mensaje
    texto_usuario = message.get("conversation") or message.get("extendedTextMessage", {}).get("text")
    if not texto_usuario:
        return {"status": "ignored", "reason": "no text content"}

    # Extraer número de teléfono
    numero_telefono = remote_jid.split("@")[0] if "@" in remote_jid else remote_jid

    # Para pruebas, usamos un tenant default. 
    tenant_default = UUID("11111111-1111-1111-1111-111111111111")
    session_id = f"wa-{numero_telefono}"

    # Tarea en segundo plano para procesar la IA y enviar respuesta
    background_tasks.add_task(
        procesar_mensaje_whatsapp,
        tenant_default,
        session_id,
        texto_usuario,
        instance_name,
        remote_jid
    )

    return {"status": "received"}

EVOLUTION_INSTANCE = "flux_agent_final"


@app.get(
    "/api/v1/whatsapp/qr",
    tags=["WhatsApp"],
    summary="Obtiene el QR code de la instancia para escanear",
)
async def whatsapp_get_qr():
    """Retorna la imagen QR en base64 para conectar WhatsApp."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            resp = await client.get(
                f"{config.evolution_api_url}/instance/connect/{EVOLUTION_INSTANCE}",
                headers={"apikey": config.evolution_api_key},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail=f"Evolution API error: {resp.text}")
            data = resp.json()
            return data
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Evolution API: {exc}")


@app.get(
    "/api/v1/whatsapp/instance-status",
    tags=["WhatsApp"],
    summary="Estado de conexión de la instancia de WhatsApp",
)
async def whatsapp_instance_status():
    """Retorna el estado actual de conexión (open, connecting, close)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{config.evolution_api_url}/instance/fetchInstances",
                headers={"apikey": config.evolution_api_key},
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=502, detail="Error al consultar Evolution API")
            instances = resp.json()
            target = next((i for i in instances if i.get("name") == EVOLUTION_INSTANCE), None)
            if not target:
                raise HTTPException(status_code=404, detail=f"Instancia '{EVOLUTION_INSTANCE}' no encontrada")
            return {
                "instance": EVOLUTION_INSTANCE,
                "connectionStatus": target.get("connectionStatus"),
                "ownerJid": target.get("ownerJid"),
                "profileName": target.get("profileName"),
            }
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Evolution API: {exc}")


@app.delete(
    "/api/v1/whatsapp/logout",
    tags=["WhatsApp"],
    summary="Cierra sesión en la instancia de WhatsApp",
)
async def whatsapp_logout():
    """Cierra sesión de WhatsApp en la instancia actual."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.delete(
                f"{config.evolution_api_url}/instance/logout/{EVOLUTION_INSTANCE}",
                headers={"apikey": config.evolution_api_key},
            )
            if resp.status_code not in (200, 201):
                logger.warning(f"Error al hacer logout en Evolution API: {resp.text}")
            return {"status": "success", "message": "Sesión cerrada correctamente"}
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"No se pudo conectar a Evolution API: {exc}")


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=config.es_desarrollo,
        log_level=config.log_level.lower(),
    )
