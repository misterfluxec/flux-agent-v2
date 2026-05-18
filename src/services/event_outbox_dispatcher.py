import json
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import SesionLocal
from core.event_bus import EventBus
from domain.events import DomainEvent
from datetime import datetime

logger = logging.getLogger(__name__)

class EventOutboxDispatcher:
    """
    Despachador del Event Outbox Pattern.
    Lee los eventos 'pending' de la base de datos (que fueron insertados atómicamente 
    con transacciones comerciales) y los envía al Redis EventBus real.
    Garantiza "At-Least-Once Delivery".
    """
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus

    async def process_pending_events(self, limit: int = 50):
        """Busca eventos pendientes y los despacha al EventBus."""
        async with SesionLocal() as db:
            # 1. Buscar y bloquear filas pendientes (FOR UPDATE SKIP LOCKED)
            # para evitar que otros workers (si los hubiera) tomen los mismos eventos.
            query = text("""
                SELECT id, tenant_id, event_type, aggregate_type, aggregate_id, payload, retry_count
                FROM event_outbox
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            """)
            events_res = await db.execute(query, {"limit": limit})
            events = events_res.fetchall()

            if not events:
                return 0

            dispatched_count = 0

            for evt in events:
                try:
                    # 2. Despachar al EventBus
                    payload_dict = json.loads(evt.payload)
                    domain_event = DomainEvent.model_validate(payload_dict)
                    await self.event_bus.publish(domain_event)

                    # 3. Marcar como despachado
                    update_q = text("""
                        UPDATE event_outbox 
                        SET status = 'dispatched', dispatched_at = :now 
                        WHERE id = :id
                    """)
                    await db.execute(update_q, {"now": datetime.utcnow(), "id": evt.id})
                    dispatched_count += 1
                    logger.debug(f"Outbox event {evt.id} ({evt.event_type}) dispatched successfully.")

                except Exception as e:
                    # 4. Manejo de Errores y Retry Count
                    logger.error(f"Failed to dispatch outbox event {evt.id}: {str(e)}")
                    new_retry = evt.retry_count + 1
                    new_status = 'failed' if new_retry >= 5 else 'pending'
                    
                    update_fail = text("""
                        UPDATE event_outbox 
                        SET status = :status, retry_count = :retry_count, error_message = :error
                        WHERE id = :id
                    """)
                    await db.execute(update_fail, {
                        "status": new_status,
                        "retry_count": new_retry,
                        "error": str(e),
                        "id": evt.id
                    })

            # Commit changes to outbox status
            await db.commit()
            return dispatched_count

# Función para usar en un BackgroundTask de FastAPI o CronJob
async def run_outbox_dispatcher():
    # En un entorno real deberíamos inyectar el redis connection
    # bus = EventBus(redis_connection)
    pass
