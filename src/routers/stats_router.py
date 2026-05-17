from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from database import obtener_sesion, configurar_rls
from auth import get_tenant_actual

router = APIRouter(prefix="/api/v1/stats", tags=["Estadísticas"])

@router.get("/overview", summary="Obtiene métricas y estadísticas del tenant actual")
async def get_stats_overview(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
) -> Dict[str, Any]:
    await configurar_rls(db, tenant_id)
    
    # 1. KPIs principales
    kpi_query = """
        SELECT 
            COUNT(*) as total_conversaciones,
            COUNT(DISTINCT lead_externo_id) as leads_capturados,
            COALESCE(AVG(sentimiento), 0) as sentimiento_promedio,
            COALESCE(SUM(tokens_entrada + tokens_salida), 0) as uso_tokens
        FROM conversaciones
        WHERE tenant_id = :tid
    """
    result = await db.execute(text(kpi_query), {"tid": str(tenant_id)})
    kpis = result.fetchone()
    
    # 2. Mensajes por día (últimos 7 días)
    # Using generate_series to ensure we get all 7 days even if empty
    days_query = """
        WITH RECURSIVE days AS (
            SELECT CURRENT_DATE - INTERVAL '6 days' AS d
            UNION ALL
            SELECT d + INTERVAL '1 day' FROM days WHERE d < CURRENT_DATE
        )
        SELECT 
            TO_CHAR(days.d, 'DD Mon') as fecha,
            COUNT(c.id) as conteo
        FROM days
        LEFT JOIN conversaciones c ON DATE(c.iniciada_en) = DATE(days.d) AND c.tenant_id = :tid
        GROUP BY days.d
        ORDER BY days.d ASC;
    """
    days_result = await db.execute(text(days_query), {"tid": str(tenant_id)})
    mensajes_por_dia = [{"fecha": row.fecha, "conteo": row.conteo} for row in days_result.fetchall()]

    # 3. Distribución de Sentimiento
    # Asumimos que sentimiento va de -1.0 a 1.0
    sentiment_query = """
        SELECT 
            COUNT(*) FILTER (WHERE sentimiento >= 0.3) as feliz,
            COUNT(*) FILTER (WHERE sentimiento > -0.3 AND sentimiento < 0.3) as neutral,
            COUNT(*) FILTER (WHERE sentimiento <= -0.3) as frustrado
        FROM conversaciones
        WHERE tenant_id = :tid AND sentimiento IS NOT NULL
    """
    sent_result = await db.execute(text(sentiment_query), {"tid": str(tenant_id)})
    sent_row = sent_result.fetchone()
    
    distribucion = [
        {"name": "Feliz 😊", "value": sent_row.feliz if sent_row else 0, "fill": "var(--success)"},
        {"name": "Neutral 😐", "value": sent_row.neutral if sent_row else 0, "fill": "var(--muted-foreground)"},
        {"name": "Frustrado 😡", "value": sent_row.frustrado if sent_row else 0, "fill": "var(--destructive)"}
    ]

    # 4. Actividad Reciente (Últimas 5 conversaciones)
    actividad_query = """
        SELECT 
            c.status,
            c.canal,
            c.iniciada_en,
            c.lead_externo_id,
            a.name as agent_name
        FROM conversaciones c
        LEFT JOIN agents a ON c.agent_id = a.id
        WHERE c.tenant_id = :tid
        ORDER BY c.iniciada_en DESC
        LIMIT 5
    """
    act_result = await db.execute(text(actividad_query), {"tid": str(tenant_id)})
    actividad_reciente = []
    for row in act_result.fetchall():
        # Formatear el tiempo relativo o dejarlo como string ISO
        # Para simplificar enviaremos la fecha como string y un mensaje de acción
        action = "Nueva conversación" if row.status == "activa" else "Conversación finalizada" if row.status == "cerrada" else "Conversación transferida"
        status = "success" if row.status in ["activa", "cerrada"] else "info"
        
        actividad_reciente.append({
            "id": str(row.iniciada_en.timestamp()),
            "action": f"{action} ({row.canal})",
            "agent": row.agent_name or "FluxBot",
            "time": row.iniciada_en.isoformat(),
            "status": status
        })

    return {
        "kpis": {
            "total_conversaciones": kpis.total_conversaciones if kpis else 0,
            "leads_capturados": kpis.leads_capturados if kpis else 0,
            "sentimiento_promedio": round(kpis.sentimiento_promedio, 2) if kpis else 0,
            "uso_tokens": kpis.uso_tokens if kpis else 0,
        },
        "mensajes_por_dia": mensajes_por_dia,
        "sentimiento_distribucion": distribucion,
        "actividad_reciente": actividad_reciente
    }

@router.get("/ingestion", summary="Obtiene métricas de ingesta y base de conocimientos")
async def get_ingestion_stats(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
) -> Dict[str, Any]:
    await configurar_rls(db, tenant_id)
    
    # Total de tokens y chunks
    query_chunks = """
        SELECT COALESCE(SUM(tokens_count), 0) as total_tokens, COUNT(*) as total_chunks
        FROM knowledge_chunks
        WHERE tenant_id = :tid
    """
    res_chunks = await db.execute(text(query_chunks), {"tid": str(tenant_id)})
    row_chunks = res_chunks.fetchone()
    
    # Total de productos activos
    query_prods = "SELECT COUNT(*) as cnt FROM productos WHERE tenant_id = :tid AND status = 'is_active'"
    res_prods = await db.execute(text(query_prods), {"tid": str(tenant_id)})
    row_prods = res_prods.fetchone()
    
    # Distribución y salud de fuentes (static vs dynamic)
    query_sources = """
        SELECT 
            COUNT(*) as total_sources,
            COUNT(*) FILTER (WHERE sync_status = 'success') as active_sources,
            COUNT(*) FILTER (WHERE source_type IN ('pdf', 'csv', 'excel', 'word')) as static_sources,
            COUNT(*) FILTER (WHERE source_type NOT IN ('pdf', 'csv', 'excel', 'word')) as dynamic_sources
        FROM synced_sources
        WHERE tenant_id = :tid
    """
    res_sources = await db.execute(text(query_sources), {"tid": str(tenant_id)})
    row_sources = res_sources.fetchone()
    
    # Métricas de tiempo de los sync logs exitosos
    query_logs = """
        SELECT 
            MAX(sync_completed_at) as last_sync_at,
            COALESCE(AVG(duration_seconds), 0) as avg_index_time_seconds
        FROM sync_logs
        WHERE tenant_id = :tid AND status = 'success'
    """
    res_logs = await db.execute(text(query_logs), {"tid": str(tenant_id)})
    row_logs = res_logs.fetchone()
    
    total_sources = row_sources.total_sources if row_sources else 0
    active_sources = row_sources.active_sources if row_sources else 0
    success_rate = round((active_sources / total_sources * 100)) if total_sources > 0 else 0
    
    # Formatear el resultado para que coincida con IngestionMetrics
    return {
        "total_tokens": int(row_chunks.total_tokens) if row_chunks else 0,
        "total_chunks": int(row_chunks.total_chunks) if row_chunks else 0,
        "active_products": int(row_prods.cnt) if row_prods else 0,
        "success_rate": success_rate,
        "active_sources": active_sources,
        "last_sync_at": row_logs.last_sync_at.isoformat() if row_logs and row_logs.last_sync_at else None,
        "avg_index_time_seconds": round(row_logs.avg_index_time_seconds, 1) if row_logs else 0,
        "dynamic_sources": row_sources.dynamic_sources if row_sources else 0,
        "static_sources": row_sources.static_sources if row_sources else 0
    }

