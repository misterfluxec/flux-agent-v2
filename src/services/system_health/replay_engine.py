from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any, List
from domain.events.registry import EventRegistry

class ReplayableEventsEngine:
    """
    Motor de Replay de Eventos (Sprint 4A.1).
    Proporciona la base para reproducir eventos fallidos de la Dead Letter Queue (DLQ),
    garantizando que ninguna transacción u operación se pierda irremediablemente.
    """
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def get_dlq_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Obtiene los eventos atrapados en la Dead Letter Queue"""
        query = text("""
            SELECT id, event_type, payload, error_reason, failed_at, retry_count
            FROM event_outbox
            WHERE tenant_id = :t AND status = 'dlq'
            ORDER BY failed_at ASC
            LIMIT :limit
        """)
        events = self.db.execute(query, {"t": self.tenant_id, "limit": limit}).fetchall()
        return [dict(e._mapping) for e in events]

    def replay_event(self, outbox_id: str) -> bool:
        """
        Intenta reproducir un evento específico desde la DLQ.
        Validando primero contra el EventRegistry si el evento es 'replayable'.
        """
        # 1. Recuperar evento
        query = text("SELECT event_type FROM event_outbox WHERE id = :id AND tenant_id = :t")
        evt = self.db.execute(query, {"id": outbox_id, "t": self.tenant_id}).fetchone()
        
        if not evt:
            raise ValueError("Event not found in DLQ")

        # 2. Validar Políticas en el Registro
        # Supongamos que event_type es 'payment.completed.v1'
        parts = evt.event_type.rsplit('.', 1)
        if len(parts) == 2:
            event_name, version = parts[0], parts[1]
            definition = EventRegistry.get_definition(event_name, version)
            
            if definition and not definition.replayable:
                raise ValueError(f"Event {evt.event_type} is marked as NON-REPLAYABLE by policy.")

        # 3. Mover de vuelta a estado 'pending' para que el OutboxDispatcher lo procese de nuevo
        update_q = text("""
            UPDATE event_outbox 
            SET status = 'pending', retry_count = retry_count + 1, updated_at = NOW() 
            WHERE id = :id AND tenant_id = :t
        """)
        self.db.execute(update_q, {"id": outbox_id, "t": self.tenant_id})
        self.db.commit()
        return True

    def archive_dlq_event(self, outbox_id: str):
        """
        Aplica la política de retención para archivar (o purgar) un evento que ya
        no puede o debe ser procesado (ej. por cambios de esquema irreversibles).
        """
        # En una arquitectura completa se movería a un Cold Storage (ej. S3).
        # Para el MVP, lo marcamos como 'archived'
        update_q = text("UPDATE event_outbox SET status = 'archived', updated_at = NOW() WHERE id = :id")
        self.db.execute(update_q, {"id": outbox_id})
        self.db.commit()
