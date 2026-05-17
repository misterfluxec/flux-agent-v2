from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from core.database import get_db_session
from core.dependencies import require_tenant_id
from services.data_sync.connection_manager import ConnectionManager
from services.data_sync.sync_engine import SyncEngine

router = APIRouter(prefix="/api/v1/intelligence", tags=["Intelligence"])
conn_manager = ConnectionManager()

@router.post("/connections")
async def create_connection(payload: dict, db: AsyncSession = Depends(get_db_session), tenant_id: str = Depends(require_tenant_id)):
    """Crea una conexión y la prueba inmediatamente"""
    
    # 1. Probar conexión antes de guardar
    test_result = await conn_manager.test_connection(payload['type'], payload['config'])
    if test_result['status'] == 'error':
        raise HTTPException(status_code=400, detail=f"Conexión fallida: {test_result.get('error', 'Unknown error')}")

    # 2. Guardar en BD usando SQL crudo ya que no tenemos SQLAlchemy Model cargado aquí explícitamente para esto
    import json
    config_json = json.dumps(payload['config'])
    
    query = text("""
        INSERT INTO data_connections (tenant_id, connection_type, name, config, status)
        VALUES (:tenant_id, :type, :name, :config, 'active')
        RETURNING id
    """)
    result = await db.execute(query, {
        "tenant_id": tenant_id,
        "type": payload['type'],
        "name": payload['name'],
        "config": config_json
    })
    new_id = result.scalar()
    await db.commit()
    
    return {"id": str(new_id), "status": "connected"}

@router.get("/connections")
async def list_connections(db: AsyncSession = Depends(get_db_session), tenant_id: str = Depends(require_tenant_id)):
    """Lista todas las conexiones con su status de salud"""
    query = text("""
        SELECT id, connection_type, name, status, sync_frequency, 
               last_sync_at, next_sync_at, total_rows_synced, last_error_message
        FROM data_connections
        WHERE tenant_id = :tenant_id
        ORDER BY created_at DESC
    """)
    result = await db.execute(query, {"tenant_id": tenant_id})
    connections = []
    for row in result.fetchall():
        connections.append({
            "id": str(row.id),
            "connection_type": row.connection_type,
            "name": row.name,
            "status": row.status,
            "sync_frequency": str(row.sync_frequency) if row.sync_frequency else "1 hour",
            "last_sync_at": row.last_sync_at.isoformat() if row.last_sync_at else None,
            "next_sync_at": row.next_sync_at.isoformat() if row.next_sync_at else None,
            "total_rows_synced": row.total_rows_synced,
            "last_error_message": row.last_error_message
        })
    return connections

@router.post("/connections/{conn_id}/sync")
async def trigger_manual_sync(conn_id: str, db: AsyncSession = Depends(get_db_session), tenant_id: str = Depends(require_tenant_id)):
    """Dispara una sincronización manual"""
    # Usamos el SyncEngine
    engine = SyncEngine(db)
    
    # Marcamos la conexion como syncing
    await db.execute(text("UPDATE data_connections SET status = 'syncing' WHERE id = :id"), {"id": conn_id})
    await db.commit()
    
    try:
        # En prod se usa background tasks (Dramatiq). Por ahora, async directo.
        await engine.execute_sync(conn_id, tenant_id)
        return {"message": "Sync completed successfully"}
    except Exception as e:
        await db.execute(text("UPDATE data_connections SET status = 'error', last_error_message = :err WHERE id = :id"), {"id": conn_id, "err": str(e)})
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Error durante sync: {str(e)}")

@router.post("/connections/{conn_id}/test")
async def test_existing_connection(conn_id: str, db: AsyncSession = Depends(get_db_session), tenant_id: str = Depends(require_tenant_id)):
    """Prueba una conexión existente"""
    query = text("SELECT connection_type, config FROM data_connections WHERE id = :id AND tenant_id = :tenant_id")
    result = await db.execute(query, {"id": conn_id, "tenant_id": tenant_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Connection not found")
        
    config_dict = row.config if isinstance(row.config, dict) else __import__("json").loads(row.config)
    test_result = await conn_manager.test_connection(row.connection_type, config_dict)
    
    if test_result['status'] == 'error':
        return {"status": "error", "message": test_result.get('error')}
        
    return {"status": "connected"}
