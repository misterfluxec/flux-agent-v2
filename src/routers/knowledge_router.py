from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from uuid import UUID
import urllib.parse

from auth import get_tenant_actual_opcional
from database import obtener_sesion, configurar_rls

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/knowledge", tags=["Conocimiento RAG"])

@router.get("", summary="Lista los documentos indexados del tenant autenticado")
async def listar_conocimiento(
    limit: int = 100,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Retorna los chunks de conocimiento del tenant actual con estadísticas por fuente."""
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

@router.delete("/{fuente_nombre}", summary="Elimina todos los chunks de un documento por su name")
async def eliminar_fuente(
    fuente_nombre: str,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Elimina todos los vectores de una fuente específica del tenant actual."""
    await configurar_rls(db, tenant_id)
    result = await db.execute(
        text("""
            DELETE FROM knowledge_chunks
            WHERE tenant_id = :tid AND fuente_nombre = :name
        """),
        {"tid": str(tenant_id), "name": fuente_nombre},
    )
    await db.commit()
    return {"eliminados": result.rowcount, "fuente": fuente_nombre}

@router.delete("", summary="Vacía todo el conocimiento (chunks y productos)")
async def vaciar_cerebro(
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Elimina todos los datos de RAG e inventario del tenant actual."""
    if not tenant_id:
        raise HTTPException(status_code=401, detail="No autenticado")

    await configurar_rls(db, tenant_id)
    
    res_chunks = await db.execute(
        text("DELETE FROM knowledge_chunks WHERE tenant_id = :tid"),
        {"tid": str(tenant_id)}
    )
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

@router.get("/{fuente_nombre}/chunks", summary="Obtiene los fragmentos extraídos de una fuente")
async def obtener_chunks_fuente(
    fuente_nombre: str,
    tenant_id: UUID = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion),
):
    await configurar_rls(db, tenant_id)
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
        "chunks": [{"id": str(c.id), "contenido": c.contenido, "sort_order": c.orden_chunk, "type": c.fuente_tipo} for c in chunks]
    }
