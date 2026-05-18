from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from config import obtener_config
from database import obtener_sesion, configurar_rls
from auth import get_tenant_actual_opcional
from sqlalchemy import text

config = obtener_config()

def register_root_endpoints(app: FastAPI):
    @app.get("/", tags=["Sistema"])
    async def raiz():
        return {
            "servicio": config.app_nombre,
            "version":  config.app_version,
            "status":   "operativo",
            "entorno":  config.app_env,
            "docs":     "/docs",
        }

    @app.get("/health", tags=["Sistema"])
    async def health_check(request: Request):
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
            await request.app.state.redis.ping()
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

        criticos_ok = estado_servicios["postgres"] == "ok" and estado_servicios["redis"] == "ok"
        hay_error_en_alguno = any(v == "error" for v in estado_servicios.values())
        return JSONResponse(
            status_code=200 if criticos_ok else 503,
            content={
                "status": "saludable" if not hay_error_en_alguno else ("degradado" if criticos_ok else "fuera_de_servicio"),
                "servicios": estado_servicios,
                "version": config.app_version,
            },
        )

    @app.get("/api/v1/knowledge", tags=["Conocimiento RAG"], summary="Lista los documentos indexados del tenant autenticado")
    async def listar_conocimiento(limit: int = 100, tenant_id: UUID = Depends(get_tenant_actual_opcional), db: AsyncSession = Depends(obtener_sesion)):
        await configurar_rls(db, tenant_id)
        result = await db.execute(
            text("""
                SELECT fuente_nombre, fuente_tipo, COUNT(*) as chunks, MAX(created_at) as ultima_ingesta
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
        total_result = await db.execute(
            text("SELECT COUNT(*) FROM knowledge_chunks WHERE tenant_id = :tid"),
            {"tid": str(tenant_id)},
        )
        total = total_result.scalar() or 0
        return {"total_chunks": total, "fuentes": fuentes, "tenant_id": str(tenant_id)}

    @app.delete("/api/v1/knowledge/{fuente_nombre}", tags=["Conocimiento RAG"])
    async def eliminar_fuente(fuente_nombre: str, tenant_id: UUID = Depends(get_tenant_actual_opcional), db: AsyncSession = Depends(obtener_sesion)):
        await configurar_rls(db, tenant_id)
        result = await db.execute(
            text("DELETE FROM knowledge_chunks WHERE tenant_id = :tid AND fuente_nombre = :name"),
            {"tid": str(tenant_id), "name": fuente_nombre},
        )
        await db.commit()
        return {"eliminados": result.rowcount, "fuente": fuente_nombre}

    @app.delete("/api/v1/knowledge", tags=["Conocimiento RAG"])
    async def vaciar_cerebro(tenant_id: UUID = Depends(get_tenant_actual_opcional), db: AsyncSession = Depends(obtener_sesion)):
        if not tenant_id:
            raise HTTPException(status_code=401, detail="No autenticado")
        await configurar_rls(db, tenant_id)
        res_chunks = await db.execute(text("DELETE FROM knowledge_chunks WHERE tenant_id = :tid"), {"tid": str(tenant_id)})
        res_prods = await db.execute(text("DELETE FROM productos WHERE tenant_id = :tid"), {"tid": str(tenant_id)})
        await db.commit()
        return {
            "mensaje": "Cerebro y catálogo vaciados correctamente.",
            "chunks_eliminados": res_chunks.rowcount,
            "productos_eliminados": res_prods.rowcount
        }

    @app.get("/api/v1/knowledge/{fuente_nombre}/chunks", tags=["Conocimiento"])
    async def obtener_chunks_fuente(fuente_nombre: str, tenant_id: UUID = Depends(get_tenant_actual_opcional), db: AsyncSession = Depends(obtener_sesion)):
        await configurar_rls(db, tenant_id)
        import urllib.parse
        fuente_decodificada = urllib.parse.unquote(fuente_nombre)
        res = await db.execute(
            text("SELECT id, contenido, orden_chunk, fuente_tipo FROM knowledge_chunks WHERE tenant_id = :tid AND fuente_nombre = :fuente ORDER BY orden_chunk ASC"),
            {"tid": str(tenant_id), "fuente": fuente_decodificada}
        )
        chunks = res.fetchall()
        return {
            "fuente": fuente_decodificada,
            "total_chunks": len(chunks),
            "chunks": [{"id": str(c.id), "contenido": c.contenido, "sort_order": c.orden_chunk, "type": c.fuente_tipo} for c in chunks]
        }
