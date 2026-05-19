from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any

from database import obtener_sesion
from auth import get_tenant_actual_opcional, PayloadToken

router = APIRouter(prefix="/api/v1", tags=["Observability & Sync"])

@router.get("/connectors/{connector_id}/status")
async def get_connector_status(
    connector_id: str,
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Retorna el status de salud en tiempo real de un conector específico."""
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    result = await db.execute(
        text("""
            SELECT status, updated_at 
            FROM connector_profiles 
            WHERE id = :cid AND tenant_id = :t
        """),
        {"cid": connector_id, "t": current_tenant.tenant_id}
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Connector not found")
        
    return {
        "id": connector_id,
        "status": row[0],
        "last_checked_at": row[1].isoformat() if row[1] else None
    }

@router.get("/connectors/{connector_id}/jobs")
async def get_connector_jobs(
    connector_id: str,
    limit: int = 10,
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Historial de Sync Jobs para un conector específico."""
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    result = await db.execute(
        text("""
            SELECT 
                id, entity_type, status, started_at, completed_at, duration_ms,
                rows_inserted, rows_updated, rows_skipped, error_count
            FROM sync_jobs
            WHERE connector_profile_id = :cid AND tenant_id = :t
            ORDER BY started_at DESC
            LIMIT :l
        """),
        {"cid": connector_id, "t": current_tenant.tenant_id, "l": limit}
    )
    
    jobs = []
    for row in result.fetchall():
        jobs.append({
            "id": str(row[0]),
            "entity_type": row[1],
            "status": row[2],
            "started_at": row[3].isoformat() if row[3] else None,
            "completed_at": row[4].isoformat() if row[4] else None,
            "duration_ms": row[5],
            "metrics": {
                "inserted": row[6],
                "updated": row[7],
                "skipped": row[8],
                "errors": row[9]
            }
        })
    return jobs

@router.get("/connectors/{connector_id}/errors")
async def get_connector_errors(
    connector_id: str,
    limit: int = 5,
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Extrae únicamente el Error Log (DLQ insights) de los últimos fallos."""
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    result = await db.execute(
        text("""
            SELECT id, started_at, error_log
            FROM sync_jobs
            WHERE connector_profile_id = :cid AND tenant_id = :t AND error_count > 0
            ORDER BY started_at DESC
            LIMIT :l
        """),
        {"cid": connector_id, "t": current_tenant.tenant_id, "l": limit}
    )
    
    errors = []
    for row in result.fetchall():
        errors.append({
            "job_id": str(row[0]),
            "occurred_at": row[1].isoformat() if row[1] else None,
            "error_log": row[2]
        })
    return errors

@router.get("/sync-metrics")
async def get_global_sync_metrics(
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    KPIs globales para el Dashboard de Connectors.
    Retorna métricas calculadas (throughput, success rate) sin forzar al frontend a procesar.
    """
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    # KPIs simples (Para DBs grandes usar vistas materializadas)
    result = await db.execute(
        text("""
            WITH stats AS (
                SELECT 
                    COUNT(*) as total_jobs,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_jobs,
                    SUM(CASE WHEN status IN ('failed', 'partial_error') AND started_at > NOW() - INTERVAL '24 HOURS' THEN 1 ELSE 0 END) as failed_24h,
                    AVG(duration_ms) as avg_duration_ms,
                    SUM(rows_inserted + rows_updated) as total_rows_processed
                FROM sync_jobs
                WHERE tenant_id = :t
            )
            SELECT * FROM stats
        """),
        {"t": current_tenant.tenant_id}
    )
    
    row = result.fetchone()
    if not row or row[0] == 0:
        return {
            "success_rate": 100.0,
            "failed_jobs_24h": 0,
            "avg_sync_duration_ms": 0,
            "total_rows_processed": 0
        }
        
    total_jobs = row[0]
    successful_jobs = row[1]
    
    return {
        "success_rate": round((successful_jobs / total_jobs) * 100, 2) if total_jobs > 0 else 100.0,
        "failed_jobs_24h": row[2] or 0,
        "avg_sync_duration_ms": int(row[3]) if row[3] else 0,
        "total_rows_processed": row[4] or 0
    }
