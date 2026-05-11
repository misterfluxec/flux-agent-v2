from sqlalchemy.orm import Session
from sqlalchemy import text
from domain.events.registry import EventRegistry, RetentionTier
import logging

logger = logging.getLogger(__name__)

class RetentionLifecycleWorker:
    """
    Fase 4B — Sprint 4B.3: Retention Lifecycle Policies.
    
    Implementa el ciclo de vida de los datos operacionales:
    - HOT -> Comprimir payloads antiguos (>7d) en el event_outbox.
    - WARM -> Archivar en operational_event_store y borrar del outbox (>90d).
    - COLD -> Archivar en S3/Cold Storage y borrar de BDD (>365d).
    """

    def __init__(self, db: Session):
        self.db = db

    def execute_lifecycle_policies(self):
        """Ejecuta todas las políticas de retención. Diseñado para correr diariamente via cron."""
        logger.info("Starting Retention Lifecycle Policies execution...")
        self._compress_hot_events()
        self._archive_warm_events()
        self._purge_cold_events()
        logger.info("Retention Lifecycle Policies completed.")

    def _compress_hot_events(self):
        """HOT (7d): Mantiene los eventos en el outbox, pero podría comprimir payloads grandes."""
        # Conceptualmente: Si un evento en outbox tiene >7d y no está en DLQ,
        # podríamos minificar su JSON o moverlo a status 'archived'.
        q = text("""
            UPDATE event_outbox
            SET status = 'archived'
            WHERE status = 'processed' 
              AND created_at < NOW() - INTERVAL '7 DAYS'
        """)
        result = self.db.execute(q)
        self.db.commit()
        logger.info(f"Compressed/Archived {result.rowcount} HOT events older than 7 days.")

    def _archive_warm_events(self):
        """WARM (90d): Mueve eventos del event_outbox al operational_event_store y los borra del outbox."""
        # Se asume que el MemoryAggregator ya los sumó. 
        # Aquí consolidamos la memoria a largo plazo.
        q_insert = text("""
            INSERT INTO operational_event_store (tenant_id, domain, event_type, correlation_id, payload, retention_tier)
            SELECT tenant_id, 'operations', event_type, correlation_id, payload, 'WARM'
            FROM event_outbox
            WHERE created_at < NOW() - INTERVAL '90 DAYS'
              AND status IN ('archived', 'processed')
        """)
        self.db.execute(q_insert)
        
        q_delete = text("""
            DELETE FROM event_outbox
            WHERE created_at < NOW() - INTERVAL '90 DAYS'
              AND status IN ('archived', 'processed')
        """)
        result = self.db.execute(q_delete)
        self.db.commit()
        logger.info(f"Moved {result.rowcount} events to WARM storage (operational_event_store).")

    def _purge_cold_events(self):
        """COLD (365d): Borra eventos de la BDD primaria. (Asume backup previo a S3 en infra)."""
        q = text("""
            DELETE FROM operational_event_store
            WHERE stored_at < NOW() - INTERVAL '365 DAYS'
        """)
        result = self.db.execute(q)
        self.db.commit()
        logger.info(f"Purged {result.rowcount} COLD events older than 365 days from operational_event_store.")
