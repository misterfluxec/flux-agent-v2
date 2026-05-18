import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from domain.events.registry import EventRegistry, PiiClassification

logger = logging.getLogger(__name__)

class EventStoreWriter:
    """
    Fase 4C — Sprint 4C.0: Event Store Pipeline Worker.
    
    Materializa la copia desde el event_outbox (transaccional) hacia
    el operational_event_store (histórico).
    Aplica metadata de retención y redacta PII según el EventRegistry.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def sync_processed_events(self, batch_size: int = 1000):
        """
        Lee eventos procesados del outbox y los copia al store.
        Este worker debe correr asíncronamente (ej. cron cada minuto o worker loop).
        """
        # Seleccionamos eventos procesados que aún no están en el store.
        # Usamos un flag o simplemente buscamos eventos recientes y hacemos upsert.
        # Para ser eficientes sin cambiar el schema del outbox (que es un estándar),
        # asumimos que borramos o marcamos los copiados, o hacemos un INSERT ignorando duplicados.
        
        # Estrategia: Leemos un batch. Los insertamos y los marcamos en outbox como 'archived'
        # o los insertamos y listos. Como la PK del store puede ser distinta, usaremos event_id original 
        # si lo tenemos, o simplemente garantizamos que outbox.status cambia.
        
        q_select = text("""
            SELECT id, tenant_id, event_type, correlation_id, payload, created_at
            FROM event_outbox
            WHERE status = 'processed'
            ORDER BY created_at ASC
            LIMIT :limit
            FOR UPDATE SKIP LOCKED
        """)
        events = self.db.execute(q_select, {"limit": batch_size}).fetchall()
        
        if not events:
            return 0
            
        inserted = 0
        for evt in events:
            definition = EventRegistry.get_definition(evt.event_type, "v1") # Default to v1 if not present in outbox schema
            domain = definition.domain.value if definition else "operations"
            tier = definition.retention_tier.value if definition else "WARM"
            
            # PII Redaction
            safe_payload = evt.payload
            if definition and definition.pii_classification in [PiiClassification.CONFIDENTIAL, PiiClassification.RESTRICTED]:
                # Redactamos el payload para el historial a largo plazo
                safe_payload = {
                    "redacted": True,
                    "reason": "PII classification restricted",
                    "original_keys": list(evt.payload.keys()) if isinstance(evt.payload, dict) else []
                }
                
            q_insert = text("""
                INSERT INTO operational_event_store (
                    tenant_id, domain, event_type, correlation_id, payload, retention_tier, stored_at
                ) VALUES (
                    :tenant_id, :domain, :event_type, :correlation_id, :payload, :tier, :stored_at
                )
            """)
            self.db.execute(q_insert, {
                "tenant_id": evt.tenant_id,
                "domain": domain,
                "event_type": evt.event_type,
                "correlation_id": evt.correlation_id,
                "payload": safe_payload, # Dict to JSONB handled by SQLAlchemy dialect usually, or we use json.dumps
                "tier": tier,
                "stored_at": evt.created_at
            })
            
            # Marcamos como archivado para no volver a leerlo
            q_update = text("UPDATE event_outbox SET status = 'archived' WHERE id = :id")
            self.db.execute(q_update, {"id": evt.id})
            
            inserted += 1

        self.db.commit()
        logger.info(f"EventStoreWriter: Synced {inserted} events to operational_event_store.")
        return inserted
