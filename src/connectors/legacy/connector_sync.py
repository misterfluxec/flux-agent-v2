import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text

# Asumiendo los modelos de Phase 1 que irían en database o domain
# from domain.business_models import CustomerCreate
from connectors.legacy.base import ERPConnectorInterface, ConnectorEntity

from domain.events import EventType, EventMetadata, DomainEvent
from core.event_bus import EventBus

logger = logging.getLogger(__name__)

class SyncEngine:
    """
    Motor de sincronización con idempotencia (Checksums MD5) y Conflict Resolution.
    Responsable de mover datos desde la Connector Layer hacia el Canonical Model.
    """
    def __init__(self, db: AsyncSession, event_bus: EventBus):
        self.db = db
        self.event_bus = event_bus

    async def _get_or_create_sync_state(self, tenant_id: str, connector_id: str, entity_type: str) -> Optional[datetime]:
        """Obtiene el último timestamp de sincronización desde la tabla sync_state (mocked here until table is created in db)"""
        try:
            # Creación on-the-fly de la tabla de control si no existe
            await self.db.execute(text("""
                CREATE TABLE IF NOT EXISTS sync_state (
                    tenant_id UUID,
                    connector_id VARCHAR(50),
                    entity_type VARCHAR(50),
                    last_sync_at TIMESTAMPTZ,
                    PRIMARY KEY (tenant_id, connector_id, entity_type)
                )
            """))
            
            result = await self.db.execute(
                text("SELECT last_sync_at FROM sync_state WHERE tenant_id = :t AND connector_id = :c AND entity_type = :e"),
                {"t": tenant_id, "c": connector_id, "e": entity_type}
            )
            row = result.fetchone()
            return row[0] if row else None
        except Exception as e:
            logger.warning(f"No se pudo acceder a sync_state: {e}")
            return None

    async def _update_sync_state(self, tenant_id: str, connector_id: str, entity_type: str):
        """Actualiza el cursor de sincronización al momento actual."""
        now = datetime.now(timezone.utc)
        await self.db.execute(text("""
            INSERT INTO sync_state (tenant_id, connector_id, entity_type, last_sync_at) 
            VALUES (:t, :c, :e, :n)
            ON CONFLICT (tenant_id, connector_id, entity_type) 
            DO UPDATE SET last_sync_at = EXCLUDED.last_sync_at
        """), {"t": tenant_id, "c": connector_id, "e": entity_type, "n": now})

    async def sync_customers(
        self, 
        tenant_id: str, 
        connector: ERPConnectorInterface,
        strategy: str = 'merge'  # 'merge', 'overwrite', 'skip'
    ) -> Dict[str, int]:
        """Sincroniza clientes desde ERP → Canonical Model."""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        connector_id = connector.__class__.__name__.lower()
        
        last_sync = await self._get_or_create_sync_state(tenant_id, connector_id, 'customers')
        customers = await connector.fetch_customers(since=last_sync)
        
        for entity in customers:
            try:
                checksum = entity.get_checksum()
                
                # Check if exists in DB
                result = await self.db.execute(
                    text("SELECT id, metadata FROM customers WHERE tenant_id = :t AND external_id = :e"),
                    {"t": tenant_id, "e": entity.external_id}
                )
                existing = result.fetchone()
                
                if existing:
                    existing_id = existing[0]
                    existing_meta = existing[1] or {}
                    last_checksum = existing_meta.get('_sync_checksum')
                    
                    if strategy == 'overwrite' or last_checksum != checksum:
                        # Update
                        await self.db.execute(text("""
                            UPDATE customers SET 
                                first_name = COALESCE(:fn, first_name),
                                last_name = COALESCE(:ln, last_name),
                                email = COALESCE(:em, email),
                                phone = COALESCE(:ph, phone),
                                metadata = metadata || :meta::jsonb,
                                updated_at = NOW()
                            WHERE id = :id
                        """), {
                            "fn": getattr(entity, 'first_name', None),
                            "ln": getattr(entity, 'last_name', None),
                            "em": getattr(entity, 'email', None),
                            "ph": getattr(entity, 'phone', None),
                            "meta": f'{{"_sync_checksum": "{checksum}"}}',
                            "id": existing_id
                        })
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    # Create
                    result = await self.db.execute(text("""
                        INSERT INTO customers (tenant_id, external_id, source_connector_id, first_name, last_name, email, phone, metadata)
                        VALUES (:t, :e, :src, :fn, :ln, :em, :ph, :meta::jsonb)
                        RETURNING id
                    """), {
                        "t": tenant_id, "e": entity.external_id, "src": connector_id,
                        "fn": getattr(entity, 'first_name', None),
                        "ln": getattr(entity, 'last_name', None),
                        "em": getattr(entity, 'email', None),
                        "ph": getattr(entity, 'phone', None),
                        "meta": f'{{"_sync_checksum": "{checksum}"}}'
                    })
                    new_id = result.fetchone()[0]
                    stats["created"] += 1
                    
                    # Emite evento de dominio
                    if self.event_bus:
                        # Dummy payload/metadata to fit DomainEvent spec
                        meta = EventMetadata(tenant_id=tenant_id, event_type=EventType.CUSTOMERS_SYNCED, aggregate_id=str(new_id))
                        await self.event_bus.publish(DomainEvent(
                            metadata=meta,
                            payload={"external_id": entity.external_id, "action": "created"}
                        ))
            except Exception as e:
                logger.error(f"Error syncing customer {entity.external_id}: {e}")
                stats["errors"] += 1
        
        await self._update_sync_state(tenant_id, connector_id, 'customers')
        await self.db.commit()
        return stats

    async def sync_products(
        self,
        tenant_id: str,
        connector: ERPConnectorInterface,
        strategy: str = 'merge'
    ) -> Dict[str, int]:
        """Sincroniza productos e inventario."""
        stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}
        connector_id = connector.__class__.__name__.lower()
        
        last_sync = await self._get_or_create_sync_state(tenant_id, connector_id, 'products')
        products = await connector.fetch_products(since=last_sync)
        
        for entity in products:
            try:
                checksum = entity.get_checksum()
                
                result = await self.db.execute(
                    text("SELECT id, metadata FROM catalog_items WHERE tenant_id = :t AND external_id = :e"),
                    {"t": tenant_id, "e": entity.external_id}
                )
                existing = result.fetchone()
                
                if existing:
                    existing_id = existing[0]
                    existing_meta = existing[1] or {}
                    last_checksum = existing_meta.get('_sync_checksum')
                    
                    if strategy == 'overwrite' or last_checksum != checksum:
                        await self.db.execute(text("""
                            UPDATE catalog_items SET 
                                name = COALESCE(:name, name),
                                base_price = COALESCE(:price, base_price),
                                stock_quantity = COALESCE(:stock, stock_quantity),
                                metadata = metadata || :meta::jsonb,
                                updated_at = NOW()
                            WHERE id = :id
                        """), {
                            "name": getattr(entity, 'name', None),
                            "price": getattr(entity, 'price', None),
                            "stock": getattr(entity, 'stock', None),
                            "meta": f'{{"_sync_checksum": "{checksum}"}}',
                            "id": existing_id
                        })
                        stats["updated"] += 1
                    else:
                        stats["skipped"] += 1
                else:
                    result = await self.db.execute(text("""
                        INSERT INTO catalog_items (tenant_id, external_id, type, name, base_price, stock_quantity, metadata)
                        VALUES (:t, :e, 'physical_product', :name, :price, :stock, :meta::jsonb)
                        RETURNING id
                    """), {
                        "t": tenant_id, "e": entity.external_id,
                        "name": getattr(entity, 'name', 'Desconocido'),
                        "price": getattr(entity, 'price', 0),
                        "stock": getattr(entity, 'stock', 0),
                        "meta": f'{{"_sync_checksum": "{checksum}"}}'
                    })
                    new_id = result.fetchone()[0]
                    stats["created"] += 1
                    
                    if self.event_bus:
                        meta = EventMetadata(tenant_id=tenant_id, event_type=EventType.CATALOG_SYNCED, aggregate_id=str(new_id))
                        await self.event_bus.publish(DomainEvent(
                            metadata=meta,
                            payload={"external_id": entity.external_id, "action": "created"}
                        ))
                        
            except Exception as e:
                logger.error(f"Error syncing product {entity.external_id}: {e}")
                stats["errors"] += 1
                
        await self._update_sync_state(tenant_id, connector_id, 'products')
        await self.db.commit()
        return stats
