from typing import Optional, Dict
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy import text

from config import obtener_config
config = obtener_config()
from database import obtener_sesion
from auth import get_tenant_actual_opcional, PayloadToken
from services.spreadsheet_sync_rag import RAGSyncEngine
from core.sensitive_logger import log_info_safe, log_error_safe
from core.encryption import EncryptionService

router = APIRouter(prefix="/api/v1/sync", tags=["Sincronización RAG"])
logger = logging.getLogger(__name__)

class SyncRequest(BaseModel):
    agent_id: str
    source_id: str
    account_id: Optional[str] = None
    column_mapping: Dict[str, str]
    sync_frequency: str = "daily"

@router.post("/sheets", status_code=status.HTTP_202_ACCEPTED)
async def trigger_sheet_sync(
    payload: SyncRequest,
    background_tasks: BackgroundTasks,
    current_tenant: PayloadToken = Depends(get_tenant_actual_opcional)
):
    """
    Dispara sincronización de fuente (Sheets o Local) hacia RAG.
    """
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    async with obtener_sesion() as db:
        async with db.begin():
            # 1. VALIDAR AGENTE
            agent = await db.execute(text("""
                SELECT id, nombre, estado, tenant_id 
                FROM agents 
                WHERE id = :agent_id AND tenant_id = :tenant_id
            """), {"agent_id": payload.agent_id, "tenant_id": current_tenant.tenant_id})
            agent_row = agent.fetchone()
            
            if not agent_row:
                raise HTTPException(404, "Agente no encontrado o no pertenece a tu cuenta")
            
            # 2. VALIDAR FUENTE (Si no es local)
            is_local = payload.account_id == "local" or payload.source_id.startswith("local_")
            
            if not is_local:
                source = await db.execute(text("""
                    SELECT id, source_type, sync_status 
                    FROM synced_sources 
                    WHERE id = :source_id AND account_id = :account_id AND tenant_id = :tenant_id
                """), {
                    "source_id": payload.source_id, 
                    "account_id": payload.account_id, 
                    "tenant_id": current_tenant.tenant_id
                })
                source_row = source.fetchone()
                
                if not source_row:
                    raise HTTPException(404, "Fuente de datos remota no encontrada")
                if source_row.sync_status == 'syncing':
                    raise HTTPException(409, "Esta fuente ya se está sincronizando")
            
            # 3. CREAR JOB DE TRACKING
            job_id = str(uuid.uuid4())
            now = datetime.utcnow()
            
            if not is_local:
                # Actualizar estado de la fuente remota
                await db.execute(text("""
                    UPDATE synced_sources 
                    SET sync_status = 'syncing', 
                        last_synced_at = :now,
                        actualizado_en = :now
                    WHERE id = :source_id
                """), {"source_id": payload.source_id, "now": now})
            
            # Registrar log inicial para el job
            await db.execute(text("""
                INSERT INTO sync_logs (id, agent_id, synced_source_id, tenant_id, status, rows_processed, sync_started_at)
                VALUES (:job_id, :agent_id, :source_id, :tenant_id, 'started', 0, :now)
            """), {
                "job_id": job_id, 
                "agent_id": payload.agent_id, 
                "source_id": payload.source_id,
                "tenant_id": current_tenant.tenant_id,
                "now": now
            })
            
            log_info_safe(
                "Sync job initiated",
                tenant_id=current_tenant.tenant_id,
                agent_id=payload.agent_id,
                source_id=payload.source_id,
                job_id=job_id,
                is_local=is_local
            )
    
    # 4. DISPARAR MOTOR RAG EN BACKGROUND
    background_tasks.add_task(
        _execute_rag_sync,
        job_id=job_id,
        agent_id=payload.agent_id,
        source_id=payload.source_id,
        account_id=payload.account_id,
        column_mapping=payload.column_mapping,
        sync_frequency=payload.sync_frequency,
        tenant_id=current_tenant.tenant_id
    )
    
    return {
        "success": True,
        "job_id": job_id,
        "status": "queued",
        "message": "Sincronización iniciada. Los productos estarán disponibles en breve.",
        "poll_url": f"/api/v1/sync/jobs/{job_id}/status"
    }

@router.get("/jobs/{job_id}/status")
async def get_job_status(job_id: str, current_tenant: PayloadToken = Depends(get_tenant_actual_opcional)):
    """Polling endpoint para saber el estado de la sincronización"""
    if not current_tenant:
        raise HTTPException(status_code=401, detail="No autenticado")
        
    async with obtener_sesion() as db:
        result = await db.execute(text("""
            SELECT status, rows_processed, error_message, sync_completed_at, sync_started_at
            FROM sync_logs
            WHERE id = :job_id AND tenant_id = :tenant_id
        """), {"job_id": job_id, "tenant_id": current_tenant.tenant_id})
        
        row = result.fetchone()
        if not row:
            raise HTTPException(404, "Job no encontrado")
            
        progress = 0
        if row.status == 'success':
            progress = 100
        elif row.status == 'failed':
            progress = 100
        elif row.status in ['started', 'syncing']:
            progress = 50
            
        return {
            "job_id": job_id,
            "status": row.status,
            "progress_percent": progress,
            "rows_processed": row.rows_processed or 0,
            "error_message": row.error_message,
            "started_at": row.sync_started_at.isoformat() if row.sync_started_at else None,
            "completed_at": row.sync_completed_at.isoformat() if row.sync_completed_at else None
        }

async def _execute_rag_sync(
    job_id: str,
    agent_id: str,
    source_id: str,
    account_id: str,
    column_mapping: dict,
    sync_frequency: str,
    tenant_id: str
):
    """Task background: Extrae -> Vectoriza -> Inserta en knowledge_chunks"""
    async with obtener_sesion() as db:
        try:
            if account_id == "local" or source_id.startswith("local_"):
                # Procesar archivo local subido previamente
                headers, rows = await RAGSyncEngine.fetch_local_file_data(source_id)
            else:
                # 1. Obtener tokens decifrados
                account = await db.execute(text("""
                    SELECT provider, access_token_encrypted, refresh_token_encrypted, token_expires_at
                    FROM connected_accounts
                    WHERE id = :account_id AND tenant_id = :tenant_id AND is_active = TRUE
                """), {"account_id": account_id, "tenant_id": tenant_id})
                acc_row = account.fetchone()
                
                if not acc_row:
                    raise ValueError("Cuenta OAuth no válida o inactiva")
                
                access_token = EncryptionService.decrypt(acc_row.access_token_encrypted)
                
                # 2. Fetch datos crudos de la hoja
                source = await db.execute(text("SELECT source_id, source_type FROM synced_sources WHERE id = :id"), {"id": source_id})
                src_row = source.fetchone()
                
                if src_row.source_type == "google_sheets":
                    headers, rows = await RAGSyncEngine.fetch_google_sheet_data(access_token, src_row.source_id)
                else:
                    headers, rows = await RAGSyncEngine.fetch_excel_online_data(access_token, src_row.source_id)
            
            if not rows:
                raise ValueError("La fuente está vacía o no tiene datos válidos")
            
            # 3. LLAMAR AL MOTOR RAG (Vectorización + Inserción)
            stats = await RAGSyncEngine.process_sheet_for_rag(
                tenant_id=tenant_id,
                agent_id=agent_id,
                synced_source_id=source_id,
                rows=rows,
                column_mapping=column_mapping
            )
            
            added = stats.get("added", 0)
            
            # 4. ACTUALIZAR ESTADO A SUCCESS
            await db.execute(text("""
                UPDATE synced_sources 
                SET sync_status = 'success',
                    last_synced_at = NOW(),
                    next_sync_at = CASE 
                        WHEN :freq = 'hourly' THEN NOW() + INTERVAL '1 hour'
                        WHEN :freq = 'daily' THEN NOW() + INTERVAL '1 day'
                        WHEN :freq = 'weekly' THEN NOW() + INTERVAL '1 week'
                        ELSE next_sync_at
                    END,
                    rows_processed = :rows_count,
                    actualizado_en = NOW()
                WHERE id = :source_id
            """), {"source_id": source_id, "freq": sync_frequency, "rows_count": added})
            
            await db.execute(text("""
                UPDATE sync_logs 
                SET status = 'success', 
                    rows_processed = :rows_count,
                    sync_completed_at = NOW()
                WHERE id = :job_id
            """), {"job_id": job_id, "rows_count": added})
            
            await db.commit()
            log_info_safe("RAG sync completed successfully", job_id=job_id, rows=added)
            
        except Exception as e:
            await db.rollback()
            log_error_safe("RAG sync failed", error=e, job_id=job_id)
            
            await db.execute(text("""
                UPDATE synced_sources 
                SET sync_status = 'failed', 
                    sync_error_message = :error,
                    actualizado_en = NOW()
                WHERE id = :source_id
            """), {"source_id": source_id, "error": str(e)[:500]})
            
            await db.execute(text("""
                UPDATE sync_logs 
                SET status = 'failed', 
                    error_message = :error,
                    sync_completed_at = NOW()
                WHERE id = :job_id
            """), {"job_id": job_id, "error": str(e)[:500]})
            await db.commit()
