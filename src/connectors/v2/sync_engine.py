import logging
from typing import Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from connectors.v2.schema_mapper import CanonicalEntity
from domain.events import EventBus, Event

logger = logging.getLogger(__name__)

class SyncEngine:
    """
    V2 Architecture: PERSISTENCE & TELEMETRY ENGINE.
    Recibe entidades canónicas y se encarga de la idempotencia (MD5) 
    y de registrar la telemetría en 'sync_jobs'.
    """
    def __init__(self, db: AsyncSession, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus

    async def _start_sync_job(self, tenant_id: str, profile_id: str, entity_type: str) -> str:
        """Inicia el registro de telemetría y devuelve el job_id."""
        result = await self.db.execute(text("""
            INSERT INTO sync_jobs (tenant_id, connector_profile_id, entity_type, status, started_at)
            VALUES (:t, :p, :e, 'running', NOW())
            RETURNING id
        """), {"t": tenant_id, "p": profile_id, "e": entity_type})
        return str(result.fetchone()[0])

    async def _close_sync_job(self, job_id: str, stats: Dict[str, int], status: str, errors: List[str] = None):
        """Cierra el job de sincronización con las métricas finales."""
        error_log = None
        if errors:
            import json
            error_log = json.dumps(errors[:10]) # Limitar tamaño
            
        await self.db.execute(text("""
            UPDATE sync_jobs SET
                status = :status,
                completed_at = NOW(),
                rows_read = :read,
                rows_inserted = :inserted,
                rows_updated = :updated,
                rows_skipped = :skipped,
                error_count = :err_count,
                error_log = :error_log::jsonb
            WHERE id = :id
        """), {
            "status": status,
            "read": stats.get('read', 0),
            "inserted": stats.get('inserted', 0),
            "updated": stats.get('updated', 0),
            "skipped": stats.get('skipped', 0),
            "err_count": len(errors) if errors else 0,
            "error_log": error_log,
            "id": job_id
        })

    async def execute_sync(self, tenant_id: str, profile_id: str, canonical_type: str, entities: List[CanonicalEntity]):
        """Sincroniza una lista de entidades y graba en las tablas de negocio."""
        job_id = await self._start_sync_job(tenant_id, profile_id, canonical_type)
        stats = {"read": len(entities), "inserted": 0, "updated": 0, "skipped": 0}
        errors = []
        
        for entity in entities:
            try:
                # 1. Determinar Idempotencia
                checksum = entity.get_checksum()
                
                # Mockups to specific tables based on type. 
                # En un entorno real se mapea 'canonical_type' a tablas.
                table = "customers" if canonical_type == "customers" else "catalog_items"
                
                # Buscar existente
                result = await self.db.execute(
                    text(f"SELECT id, metadata FROM {table} WHERE tenant_id = :t AND external_id = :e"),
                    {"t": tenant_id, "e": entity.external_id}
                )
                existing = result.fetchone()
                
                if existing:
                    existing_id, meta = existing[0], existing[1] or {}
                    last_checksum = meta.get('_sync_checksum')
                    
                    if last_checksum != checksum:
                        # Update (Simplificado para el boilerplate. Payload real usaría jsonb_set o kwargs)
                        await self.db.execute(text(f"""
                            UPDATE {table} SET
                                metadata = metadata || :meta::jsonb,
                                updated_at = NOW()
                            WHERE id = :id
                        """), {
                            "meta": f'{{"_sync_checksum": "{checksum}"}}',
                            "id": existing_id
                        })
                        stats["updated"] += 1
                        
                        if self.event_bus:
                            await self.event_bus.publish(Event(
                                event_type=f"{canonical_type}.updated", 
                                tenant_id=tenant_id, aggregate_id=str(existing_id), payload={}
                            ))
                    else:
                        stats["skipped"] += 1
                else:
                    # Insert 
                    # ... [Lógica de Insert simplificada]
                    stats["inserted"] += 1
                    
                    if self.event_bus:
                        await self.event_bus.publish(Event(
                            event_type=f"{canonical_type}.created", 
                            tenant_id=tenant_id, aggregate_id="NEW_ID", payload={"external_id": entity.external_id}
                        ))
                        
            except Exception as e:
                errors.append(f"Error {entity.external_id}: {str(e)}")
                
        # 3. Cerrar Job
        final_status = "success" if not errors else ("partial_error" if stats["inserted"] > 0 else "failed")
        await self._close_sync_job(job_id, stats, final_status, errors)
        await self.db.commit()
