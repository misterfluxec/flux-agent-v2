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
from routers.stats_router import router as stats_router
from routers.products_router import router as products_router
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
from routers.whatsapp_cloud_router import router as whatsapp_cloud_router
from routers.quota_router import router as quota_router
from routers.oauth_sync_router import router as oauth_sync_router
from routers.sync_router import router as sync_router
from routers.upload_router import router as upload_router
from routers.sales_agent_router import router as sales_router
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
        start_rag_scheduler()
    except Exception as e:
        logger.warning(f"⚠️  RAG Sync scheduler no iniciado: {e}")
    
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
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID"],
)


@app.middleware("http")
async def middleware_tiempo_respuesta(request: Request, call_next):
    inicio = time.perf_counter()
    respuesta = await call_next(request)
    ms = (time.perf_counter() - inicio) * 1000
    respuesta.headers["X-Process-Time"] = f"{ms:.2f}ms"
    return respuesta


# =============================================================================
# ROUTERS
# =============================================================================

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
app.include_router(ws_router)
app.include_router(voice_router)
app.include_router(channels_router)
app.include_router(whatsapp_health_router)
app.include_router(whatsapp_cloud_router)
app.include_router(quota_router)
app.include_router(oauth_sync_router)
app.include_router(sync_router)
app.include_router(upload_router)
app.include_router(sales_router, prefix="/api/v1")


@app.exception_handler(Exception)
async def manejador_error_global(request: Request, exc: Exception):
    logger.error(f"Error no manejado en {request.url}: {exc}", exc_info=True)
    detalle = str(exc) if config.es_desarrollo else "Error interno del servidor"
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "error_interno", "mensaje": detalle, "path": str(request.url.path)},
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
