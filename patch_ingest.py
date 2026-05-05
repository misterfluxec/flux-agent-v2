import re

with open("src/main.py", "r") as f:
    content = f.read()

# I will write the new background worker and the updated endpoint
new_code = """
# =============================================================================
# BACKGROUND TASK: Ingesta Asíncrona
# =============================================================================
import uuid
import os
import asyncio
from database import SesionLocal

async def actualizar_estado_redis(job_id: str, estado: str, progreso: int, mensaje: str = "", metadata: dict = None):
    try:
        import redis.asyncio as aioredis
        import json
        r = aioredis.from_url(config.redis_url, decode_responses=True)
        data = {
            "estado": estado,
            "progreso": progreso,
            "mensaje": mensaje,
        }
        if metadata:
            data.update(metadata)
        await r.setex(f"ingest_job:{job_id}", 86400, json.dumps(data))
        await r.aclose()
    except Exception as e:
        logger.error(f"Error actualizando Redis para job {job_id}: {e}")

async def procesar_ingesta_background(
    job_id: str,
    tenant_id: UUID,
    agent_id: Optional[UUID],
    archivo_ruta: Optional[str],
    archivo_nombre: Optional[str],
    extension: Optional[str],
    url: Optional[str]
):
    from services.ingestion import ServicioIngesta
    servicio = ServicioIngesta()
    
    await actualizar_estado_redis(job_id, "procesando", 10, "Iniciando procesamiento...")
    
    async with SesionLocal() as db:
        await configurar_rls(db, tenant_id)
        try:
            chunks_guardados = 0
            if archivo_ruta and archivo_nombre:
                with open(archivo_ruta, "rb") as f:
                    contenido = f.read()
                
                await actualizar_estado_redis(job_id, "procesando", 30, f"Extrayendo texto de {extension}...")
                
                if extension == "pdf":
                    chunks_guardados = await servicio.procesar_pdf(db, contenido, archivo_nombre, tenant_id, agent_id)
                elif extension == "txt":
                    chunks_guardados = await servicio.procesar_txt(db, contenido, archivo_nombre, tenant_id, agent_id)
                elif extension == "csv":
                    chunks_guardados = await servicio.procesar_csv(db, contenido, archivo_nombre, tenant_id, agent_id)
                else:  # xlsx / xls
                    chunks_guardados = await servicio.procesar_excel(db, contenido, archivo_nombre, tenant_id, agent_id)
            elif url:
                await actualizar_estado_redis(job_id, "procesando", 30, "Descargando web...")
                chunks_guardados = await servicio.procesar_url(db, url, tenant_id, agent_id)
            
            await db.commit()
            await actualizar_estado_redis(job_id, "completado", 100, f"✅ {chunks_guardados} fragmentos indexados correctamente.", {"chunks": chunks_guardados})
            logger.info(f"Ingesta {job_id} completada exitosamente.")
            
        except Exception as exc:
            await db.rollback()
            logger.error(f"Error en ingesta background {job_id}: {exc}", exc_info=True)
            await actualizar_estado_redis(job_id, "error", 0, f"Error: {str(exc)}")

# =============================================================================
# ENDPOINT: POST /api/v1/ingest
# =============================================================================

EXTENSIONES_PERMITIDAS = {"pdf", "xlsx", "xls", "csv", "txt"}

from fastapi import BackgroundTasks

@app.post(
    "/api/v1/ingest",
    tags=["Ingesta RAG"],
    summary="Sube un archivo o URL para entrenar al agente (Asíncrono)",
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingestar_conocimiento(
    background_tasks: BackgroundTasks,
    archivo:   Optional[UploadFile]  = File(None,  description="Archivo PDF, XLSX, CSV o TXT"),
    url:       Optional[str]         = Form(None,  description="URL de página web a indexar"),
    agent_id:  Optional[UUID]        = Form(None,  description="UUID del agente (opcional)"),
    tenant_id: UUID                  = Depends(get_tenant_actual_opcional),
    db:        AsyncSession          = Depends(obtener_sesion),
):
    \"\"\"
    Pipeline de Ingesta RAG Asíncrono.

    Retorna un `job_id` que puede ser consultado para ver el progreso.
    \"\"\"
    if not archivo and not url:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debes proporcionar un archivo o una URL, no ambos ni ninguno.",
        )

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
        archivo_ruta = f"uploads/knowledge/{job_id}_{archivo.filename}"
        with open(archivo_ruta, "wb") as f:
            f.write(contenido)
            
    # Iniciar estado en Redis
    await actualizar_estado_redis(job_id, "pendiente", 0, "En cola...")

    # Enviar a background
    background_tasks.add_task(
        procesar_ingesta_background,
        job_id, tenant_id, agent_id, archivo_ruta, archivo.filename if archivo else None, extension, url
    )

    return {
        "job_id": job_id,
        "estado": "procesando",
        "fuente": archivo.filename if archivo else url,
        "mensaje": "La ingesta ha comenzado en segundo plano.",
    }

# =============================================================================
# ENDPOINT: GET /api/v1/ingest/status/{job_id}
# =============================================================================
@app.get(
    "/api/v1/ingest/status/{job_id}",
    tags=["Ingesta RAG"],
    summary="Obtiene el estado de un trabajo de ingesta",
)
async def obtener_estado_ingesta(job_id: str):
    try:
        import redis.asyncio as aioredis
        import json
        r = aioredis.from_url(config.redis_url, decode_responses=True)
        data = await r.get(f"ingest_job:{job_id}")
        await r.aclose()
        
        if not data:
            return {"estado": "desconocido", "progreso": 0, "mensaje": "Job no encontrado o expirado"}
            
        return json.loads(data)
    except Exception as e:
        logger.error(f"Error consultando Redis para job {job_id}: {e}")
        return {"estado": "error", "mensaje": "Error consultando estado"}

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
        text(\"\"\"
            SELECT id, contenido, orden_chunk, fuente_tipo 
            FROM knowledge_chunks 
            WHERE tenant_id = :tid AND fuente_nombre = :fuente
            ORDER BY orden_chunk ASC
        \"\"\"),
        {"tid": str(tenant_id), "fuente": fuente_decodificada}
    )
    chunks = res.fetchall()
    return {
        "fuente": fuente_decodificada,
        "total_chunks": len(chunks),
        "chunks": [{"id": str(c.id), "contenido": c.contenido, "orden": c.orden_chunk, "tipo": c.fuente_tipo} for c in chunks]
    }
"""

start_marker = "# =============================================================================\n# ENDPOINT: POST /api/v1/ingest\n# =============================================================================\n"
end_marker = "# =============================================================================\n# SCHEMAS DE CHAT\n# =============================================================================\n"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker)

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_code + "\n" + content[end_idx:]
    with open("src/main.py", "w") as f:
        f.write(new_content)
    print("Successfully patched main.py")
else:
    print("Could not find markers.")
