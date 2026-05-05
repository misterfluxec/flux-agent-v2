import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from database import obtener_sesion
from services.spreadsheet_sync_rag import RAGSyncEngine
from core.encryption import EncryptionService

logger = logging.getLogger(__name__)

# Instancia global del scheduler
scheduler = AsyncIOScheduler()

async def sync_all_pending_sheets():
    """Busca hojas pendientes de sync y ejecuta el motor RAG"""
    logger.info("🔄 Buscando inventarios pendientes para sincronización RAG...")
    try:
        async with obtener_sesion() as db:
            # Obtener fuentes que ya les toca sincronizarse
            result = await db.execute(text("""
                SELECT s.id, s.tenant_id, s.agent_id, s.source_type, s.source_id, s.column_mapping,
                       a.access_token_encrypted, a.provider
                FROM synced_sources s
                JOIN connected_accounts a ON s.account_id = a.id
                WHERE s.next_sync_at <= NOW() AND a.is_active = TRUE
            """))
            sources = result.fetchall()
            
            if not sources:
                return
                
            logger.info(f"🔄 Encontradas {len(sources)} fuentes para sincronizar.")
            
            for source in sources:
                try:
                    await db.execute(text("UPDATE synced_sources SET sync_status = 'syncing' WHERE id = :id"), {"id": source.id})
                    await db.commit()
                    
                    access_token = EncryptionService.decrypt(source.access_token_encrypted)
                    
                    if source.source_type == "google_sheets":
                        _, rows = await RAGSyncEngine.fetch_google_sheet_data(access_token, source.source_id)
                    else:
                        _, rows = await RAGSyncEngine.fetch_excel_online_data(access_token, source.source_id)
                        
                    stats = await RAGSyncEngine.process_sheet_for_rag(
                        tenant_id=source.tenant_id,
                        agent_id=source.agent_id,
                        synced_source_id=source.id,
                        rows=rows,
                        column_mapping=source.column_mapping
                    )
                    
                    # Calcular el siguiente tiempo de sincronización (asumiendo diario por defecto)
                    await db.execute(text("""
                        UPDATE synced_sources 
                        SET sync_status = 'success', 
                            last_synced_at = NOW(), 
                            next_sync_at = NOW() + INTERVAL '1 day',
                            rows_processed = :rows,
                            actualizado_en = NOW()
                        WHERE id = :id
                    """), {"id": source.id, "rows": len(rows)})
                    
                    # Guardar log
                    await db.execute(text("""
                        INSERT INTO sync_logs (synced_source_id, tenant_id, agent_id, status, rows_fetched, rows_processed)
                        VALUES (:source_id, :tenant_id, :agent_id, 'success', :fetched, :processed)
                    """), {
                        "source_id": source.id,
                        "tenant_id": source.tenant_id,
                        "agent_id": source.agent_id,
                        "fetched": len(rows),
                        "processed": stats["added"]
                    })
                    await db.commit()
                    
                    logger.info(f"✅ Sincronización exitosa para fuente {source.id}: {stats['added']} chunks agregados.")
                    
                except Exception as e:
                    logger.error(f"❌ Error sincronizando fuente {source.id}: {e}")
                    await db.execute(text("UPDATE synced_sources SET sync_status = 'failed' WHERE id = :id"), {"id": source.id})
                    await db.execute(text("""
                        INSERT INTO sync_logs (synced_source_id, tenant_id, agent_id, status, error_message)
                        VALUES (:source_id, :tenant_id, :agent_id, 'failed', :error)
                    """), {
                        "source_id": source.id,
                        "tenant_id": source.tenant_id,
                        "agent_id": source.agent_id,
                        "error": str(e)
                    })
                    await db.commit()
                    
    except Exception as e:
        logger.error(f"Error crítico en el proceso de sincronización RAG: {e}")

def start_scheduler():
    """Configura y arranca el scheduler"""
    if not scheduler.running:
        # Configurar para que corra cada hora y revise qué toca sincronizar
        scheduler.add_job(sync_all_pending_sheets, CronTrigger(hour='*'), id='sheets_rag_sync', replace_existing=True)
        scheduler.start()
        logger.info("⏰ Scheduler de sincronización RAG (APScheduler) iniciado exitosamente.")

def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown()
        logger.info("⏰ Scheduler RAG detenido.")
