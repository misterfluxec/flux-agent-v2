import logging
import asyncio
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks, File, Form, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from config import obtener_config
from database import obtener_sesion, configurar_rls
from auth import get_tenant_actual_opcional
from core.task_runner import task_runner
from core.ws_manager import manager

logger = logging.getLogger(__name__)
config = obtener_config()
router = APIRouter(prefix="/api/v1/ingest", tags=["Ingesta RAG"])
ws_router = APIRouter(tags=["WebSockets"])

# =============================================================================
# ENDPOINT WEBSOCKET: PROGRESS PUBLISHING
# =============================================================================
@ws_router.websocket("/ws/ingestion/{tenant_id}")
async def websocket_ingestion_endpoint(websocket: WebSocket, tenant_id: str):
    await manager.connect(websocket, tenant_id)
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(config.redis_url, decode_responses=True)
        pubsub = r.pubsub()
        await pubsub.subscribe(f"tenant:{tenant_id}:ingest_progress")
        
        # Tarea de escucha de Redis PubSub para enviar mensajes WS
        async def listen_redis():
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = message["data"]
                    # Data es un string JSON de update_progress
                    import json
                    await manager.broadcast_to_tenant(tenant_id, json.loads(data))
                    
        redis_task = asyncio.create_task(listen_redis())

        while True:
            # Mantener la conexion viva, esperar desconexión
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, tenant_id)
        redis_task.cancel()
        await pubsub.unsubscribe()
        await r.aclose()
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, tenant_id)
        if 'redis_task' in locals():
            redis_task.cancel()

# =============================================================================
# TAREA EN SEGUNDO PLANO
# =============================================================================
EXTENSIONES_PERMITIDAS = {"pdf", "xlsx", "xls", "csv", "txt"}

@task_runner.run_async
async def procesar_ingesta_background(
    job_id: str,
    tenant_id: UUID,
    agent_id: Optional[UUID],
    archivo_ruta: Optional[str],
    archivo_nombre: Optional[str],
    extension: Optional[str],
    url: Optional[str],
    task_id: str = None
):
    # Nota: `task_id` es inyectado por `@task_runner.run_async`
    from services.ingestion import ServicioIngesta
    from database import SesionLocal
    servicio = ServicioIngesta()
    
    tenant_str = str(tenant_id)
    task_runner.update_progress(task_id, 10, "procesando", "Iniciando procesamiento...", "processing", tenant_str)
    
    async with SesionLocal() as db:
        await configurar_rls(db, tenant_id)
        try:
            chunks_guardados = 0
            if archivo_ruta and archivo_nombre:
                with open(archivo_ruta, "rb") as f:
                    contenido = f.read()
                
                task_runner.update_progress(task_id, 30, "extrayendo", f"Extrayendo texto de {extension}...", "processing", tenant_str)
                
                # Para MVP pasamos task_id y task_runner si queremos que los metodos internos logueen. 
                # De momento asumo que los metodos internos se encargan o devuelven rapido.
                if extension == "pdf":
                    chunks_guardados = await servicio.procesar_pdf(db, contenido, archivo_nombre, tenant_id, agent_id)
                elif extension == "txt":
                    chunks_guardados = await servicio.procesar_txt(db, contenido, archivo_nombre, tenant_id, agent_id)
                elif extension == "csv":
                    chunks_guardados = await servicio.procesar_csv(db, contenido, archivo_nombre, tenant_id, agent_id)
                else:  # xlsx / xls
                    chunks_guardados = await servicio.procesar_excel(db, contenido, archivo_nombre, tenant_id, agent_id)
            elif url:
                task_runner.update_progress(task_id, 30, "descargando", "Descargando web...", "processing", tenant_str)
                chunks_guardados = await servicio.procesar_url(db, url, tenant_id, agent_id)
            
            await db.commit()
            task_runner.update_progress(task_id, 100, "completado", f"✅ {chunks_guardados} fragmentos indexados correctamente.", "completed", tenant_str)
            logger.info(f"Ingesta {job_id} completada exitosamente.")
            
        except Exception as exc:
            await db.rollback()
            logger.error(f"Error en ingesta background {job_id}: {exc}", exc_info=True)
            task_runner.update_progress(task_id, 0, "error", f"Error: {str(exc)}", "error", tenant_str)


# =============================================================================
# ENDPOINT HTTP: INICIAR INGESTA
# =============================================================================
@router.post("/start", status_code=status.HTTP_202_ACCEPTED)
async def iniciar_ingesta(
    background_tasks: BackgroundTasks,
    archivo:   Optional[UploadFile]  = File(None,  description="Archivo PDF, XLSX, CSV o TXT"),
    url:       Optional[str]         = Form(None,  description="URL de página web a indexar"),
    agent_id:  Optional[UUID]        = Form(None,  description="UUID del agente (opcional)"),
    tenant_id: UUID                  = Depends(get_tenant_actual_opcional),
    db:        AsyncSession          = Depends(obtener_sesion),
):
    if not archivo and not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes proporcionar un archivo o una URL, no ambos ni ninguno.",
        )

    # job_id se pasa a task_runner, que usa internamente un `task_id`.
    # Usaremos el job_id como task_id para simplificar.
    job_id = str(uuid.uuid4())
    archivo_ruta = None
    extension = None

    if archivo:
        extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
        if extension not in EXTENSIONES_PERMITIDAS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Tipo de archivo no soportado: .{extension}. Permitidos: {EXTENSIONES_PERMITIDAS}",
            )
            
        contenido = await archivo.read()
        max_bytes = config.max_file_size_mb * 1024 * 1024
        if len(contenido) > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Archivo demasiado grande. Máximo: {config.max_file_size_mb}MB",
            )
            
        # Guardar archivo físico en el servidor
        import os
        os.makedirs("uploads/knowledge", exist_ok=True)
        archivo_ruta = f"uploads/knowledge/{job_id}_{archivo.filename}"
        with open(archivo_ruta, "wb") as f:
            f.write(contenido)
            
    # Iniciar status inicial (TaskRunner ya lo hace pero para que la UI lo vea rápido)
    task_runner.update_progress(job_id, 0, "pending", "En cola...", "pending", str(tenant_id))

    # Enviar a background. Al estar decorado, procesar_ingesta_background ya recibe `task_id` o lo genera
    # Pero le pasaremos el kwarg task_id=job_id para que utilice el mismo id.
    # En FastAPI, BackgroundTasks necesita corutinas o funciones normales. El TaskRunner (si use_celery=False) 
    # es asíncrono y se ejecuta correctamente en BackgroundTasks si lo pasamos tal cual?
    # Wait, TaskRunner usa `await task_func(...)` lo cual en FastAPI BackgroundTasks necesita `add_task(async_func, ...)`
    # Así que pasaremos la función decorada a background_tasks.
    background_tasks.add_task(
        procesar_ingesta_background,
        job_id, tenant_id, agent_id, archivo_ruta, archivo.filename if archivo else None, extension, url, task_id=job_id
    )

    return {
        "job_id": job_id,
        "status": "procesando",
        "fuente": archivo.filename if archivo else url,
        "mensaje": "La ingesta ha comenzado en segundo plano.",
    }

# =============================================================================
# ENDPOINT HTTP: TEST SEARCH
# =============================================================================
from pydantic import BaseModel
class TestSearchRequest(BaseModel):
    query: str
    match_count: int = 5

@router.post("/test-search", tags=["Conocimiento RAG"], summary="Prueba de Búsqueda Híbrida")
async def test_search(
    req: TestSearchRequest,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    from sqlalchemy import text
    from config import obtener_config
    # Generar embedding local o vía API según config
    # Simulamos o llamamos a ollama/nomic según el proyecto
    # En MVP si el config usa embeddings se generaría
    # Por ahora haremos un placeholder
    return {"message": "Endpoint de test implementado. Requiere generador de embedding."}
