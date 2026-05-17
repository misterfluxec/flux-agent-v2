import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from sqlalchemy import text
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class StoredEvent(BaseModel):
    id: str
    aggregate_id: str
    tenant_id: str
    event_type: str
    payload: Dict[str, Any]
    created_at: datetime
    version: int
    schema_version: int = 1

class EventStore:
    """
    Event Sourcing Append-Only Store.
    Persiste eventos de dominio en PostgreSQL para reconstrucción del status.
    """
    
    def __init__(self, db_session_maker):
        self.db_session_maker = db_session_maker

    async def append(self, aggregate_id: str, tenant_id: str, event_type: str, payload: Dict[str, Any], connection=None, schema_version: int = 1) -> str:
        """
        Agrega un nuevo evento al store de manera inmutable (append-only).
        Si connection es None, usa db_session_maker, de lo contrario asume que ya estamos en una DB Transaction.
        """
        import json
        
        async def _do_append(db):
            # Obtener el MAX(version) actual de forma atómica (optimistic concurrency)
            # En un sistema real de alto tráfico se usaría Sequence o un Constraint Único en (aggregate_id, version)
            version_query = text("SELECT COALESCE(MAX(version), 0) + 1 FROM event_store WHERE aggregate_id = :agg_id")
            result = await db.execute(version_query, {"agg_id": aggregate_id})
            next_version = result.scalar()
            
            insert_query = text("""
                INSERT INTO event_store (aggregate_id, tenant_id, event_type, payload, version, schema_version, created_at)
                VALUES (:aggregate_id, :tenant_id, :event_type, :payload, :version, :schema_version, NOW())
                RETURNING id
            """)
            
            params = {
                "aggregate_id": aggregate_id,
                "tenant_id": tenant_id,
                "event_type": event_type,
                "payload": json.dumps(payload),
                "version": next_version,
                "schema_version": schema_version
            }
            
            res = await db.execute(insert_query, params)
            event_id = res.scalar()
            logger.debug(f"[EventStore] Appended event {event_type} for aggregate {aggregate_id} (v{next_version}, schema v{schema_version})")
            return str(event_id)

        if connection:
            return await _do_append(connection)
        else:
            async with self.db_session_maker() as db:
                event_id = await _do_append(db)
                await db.commit()
                return event_id

    async def replay(self, aggregate_id: str, from_version: int = 0) -> List[StoredEvent]:
        """
        Reconstruye la historia de un aggregate_id.
        """
        import json
        
        async with self.db_session_maker() as db:
            query = text("""
                SELECT id, aggregate_id, tenant_id, event_type, payload, created_at, version, schema_version
                FROM event_store
                WHERE aggregate_id = :aggregate_id AND version >= :from_version
                ORDER BY version ASC
            """)
            
            result = await db.execute(query, {"aggregate_id": aggregate_id, "from_version": from_version})
            rows = result.fetchall()
            
            events = []
            for r in rows:
                events.append(StoredEvent(
                    id=str(r.id),
                    aggregate_id=str(r.aggregate_id),
                    tenant_id=str(r.tenant_id),
                    event_type=r.event_type,
                    payload=r.payload if isinstance(r.payload, dict) else json.loads(r.payload),
                    created_at=r.created_at,
                    version=r.version,
                    schema_version=getattr(r, 'schema_version', 1)
                ))
            return events

    async def snapshot(self, aggregate_id: str) -> Optional[Dict[str, Any]]:
        """
        Opcional: Obtener un snapshot para evitar un replay masivo.
        No implementado en esta primera versión (depende de CQRS o proyecciones).
        """
        pass
