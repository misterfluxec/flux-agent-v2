import logging
import dramatiq
from datetime import datetime
from sqlalchemy import text
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.database import async_session_factory
from tasks.followup_worker import procesar_seguimiento_cotizacion

logger = logging.getLogger(__name__)

async def check_pending_followups():
    """
    Busca follow_ups programados que ya deberían haberse enviado
    y los encola en el worker de Dramatiq para su ejecución asíncrona.
    """
    logger.info("🔍 Buscando follow_ups de cotizaciones pendientes...")
    try:
        async with async_session_factory() as session:
            # Desactivar RLS si es necesario o usar bypass
            # Asumiendo que esta es una tarea del sistema sin tenant
            
            # Buscar follow_ups programados vencidos
            query = text("""
                SELECT id 
                FROM follow_ups 
                WHERE status = 'programado' 
                AND scheduled_send_at <= NOW()
                FOR UPDATE SKIP LOCKED
            """)
            
            result = await session.execute(query)
            pendientes = result.fetchall()
            
            if not pendientes:
                return
                
            logger.info(f"Encontrados {len(pendientes)} follow_ups pendientes. Encolando...")
            
            # Marcamos en progreso y encolamos
            ids_a_procesar = [row.id for row in pendientes]
            
            if ids_a_procesar:
                update_query = text("""
                    UPDATE follow_ups 
                    SET status = 'en_proceso', updated_at = NOW()
                    WHERE id = ANY(:ids)
                """)
                await session.execute(update_query, {"ids": [str(i) for i in ids_a_procesar]})
                await session.commit()
                
                # Encolar en Dramatiq
                for seg_id in ids_a_procesar:
                    procesar_seguimiento_cotizacion.send(str(seg_id))
                    
                logger.info(f"✅ {len(ids_a_procesar)} follow_ups enviados a Dramatiq")
    except Exception as e:
        logger.error(f"Error checking pending followups: {e}")

def setup_followup_scheduler(scheduler: AsyncIOScheduler):
    """
    Registra el trabajo de polling en el APScheduler principal.
    """
    scheduler.add_job(
        check_pending_followups,
        'interval',
        minutes=5,  # Revisa cada 5 minutos
        id='poll_seguimientos_cotizacion',
        replace_existing=True
    )
    logger.info("📅 Follow-up scheduler registrado (intervalo: 5m)")
