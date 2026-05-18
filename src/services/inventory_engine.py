import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.commerce_transaction_manager import CommerceTransactionManager
from domain.commerce_states import InventoryMovementType, InventoryReasonCode, ReservationType
from domain.events.inventory_events import InventoryMovementEventV1

class InventoryConcurrencyError(Exception):
    pass

class InventoryEngineV2:
    """
    Inventory Engine de FluxAgent V2 (Enterprise).
    - Escribe en el Ledger Inmutable con Correlation Tracing.
    - Actualiza Snapshot con Optimistic Concurrency (version_number).
    - Respeta las políticas del Tenant (allow_backorders).
    """
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tx_manager = CommerceTransactionManager(db, tenant_id)

    async def record_movement(
        self,
        catalog_item_id: str,
        movement_type: InventoryMovementType,
        reason_code: InventoryReasonCode,
        quantity: int,
        correlation_id: str,
        source_type: str,
        source_id: Optional[str] = None,
        actor_id: str = 'system',
        reservation_type: Optional[ReservationType] = None
    ) -> str:
        
        # 1. Obtener Políticas del Tenant
        policy_q = text("SELECT allow_backorders FROM tenant_inventory_policies WHERE tenant_id = :tenant_id")
        policy_res = await self.db.execute(policy_q, {"tenant_id": self.tenant_id})
        policy = policy_res.fetchone()
        allow_backorders = policy.allow_backorders if policy else False

        # 2. Lockear Snapshot for Update
        snapshot_q = text("""
            SELECT id, current_stock, reserved_stock, available_stock, version_number 
            FROM inventory_snapshots 
            WHERE tenant_id = :tenant_id AND catalog_item_id = :item_id
            FOR UPDATE
        """)
        snapshot_res = await self.db.execute(snapshot_q, {"tenant_id": self.tenant_id, "item_id": catalog_item_id})
        snapshot = snapshot_res.fetchone()

        current_stock = snapshot.current_stock if snapshot else 0
        reserved_stock = snapshot.reserved_stock if snapshot else 0
        current_version = snapshot.version_number if snapshot else 0

        # 3. Calcular impacto
        delta_current = 0
        delta_reserved = 0

        if movement_type in ('IMPORT', 'RETURN', 'TRANSFER', 'ADJUSTMENT', 'SYNC_CORRECTION'):
            delta_current = quantity
        elif movement_type == 'RESERVE':
            delta_reserved = quantity
        elif movement_type == 'RELEASE':
            delta_reserved = -quantity
        elif movement_type == 'COMMIT':
            delta_current = -quantity
            delta_reserved = -quantity
        elif movement_type == 'REFUND':
            delta_current = quantity

        new_current = current_stock + delta_current
        new_reserved = reserved_stock + delta_reserved
        new_available = new_current - new_reserved

        # 4. Business Validation (Negative Stock vs Policy)
        if new_available < 0 and not allow_backorders and movement_type != 'SYNC_CORRECTION':
            raise ValueError(
                f"Insufficient stock for item {catalog_item_id}. "
                f"Available: {current_stock - reserved_stock}, Requested Delta: {quantity}. "
                f"Backorders not allowed for tenant {self.tenant_id}."
            )

        # 5. Atomic DB Transaction
        ledger_id = str(uuid.uuid4())
        
        async with self.tx_manager.atomic_transaction(
            action_name=f"inventory.{movement_type.lower()}",
            actor_type="system",
            actor_id=actor_id,
            target_resource="catalog_item",
            target_id=catalog_item_id
        ) as tx:

            # A. Escribir Ledger
            await self.db.execute(text("""
                INSERT INTO inventory_ledger 
                (id, tenant_id, catalog_item_id, correlation_id, source_type, source_id, 
                 movement_type, reservation_type, reason_code, quantity, created_by)
                VALUES 
                (:id, :tenant_id, :item_id, :correlation_id, :source_type, :source_id, 
                 :type, :res_type, :reason, :qty, :actor)
            """), {
                "id": ledger_id,
                "tenant_id": self.tenant_id,
                "item_id": catalog_item_id,
                "correlation_id": correlation_id,
                "source_type": source_type,
                "source_id": source_id,
                "type": movement_type,
                "res_type": reservation_type,
                "reason": reason_code,
                "qty": quantity,
                "actor": actor_id
            })

            # B. Upsert Snapshot con Optimistic Concurrency
            new_version = current_version + 1
            if snapshot:
                # Update existente validando versión
                result = await self.db.execute(text("""
                    UPDATE inventory_snapshots 
                    SET current_stock = :cur, 
                        reserved_stock = :res, 
                        last_ledger_id = :ledger_id, 
                        version_number = :new_ver,
                        updated_at = NOW()
                    WHERE id = :snap_id AND version_number = :old_ver
                """), {
                    "cur": new_current,
                    "res": new_reserved,
                    "ledger_id": ledger_id,
                    "new_ver": new_version,
                    "snap_id": snapshot.id,
                    "old_ver": current_version
                })
                if result.rowcount == 0:
                    raise InventoryConcurrencyError(f"Concurrency error updating snapshot for item {catalog_item_id}")
            else:
                # Insert nuevo
                await self.db.execute(text("""
                    INSERT INTO inventory_snapshots 
                    (tenant_id, catalog_item_id, current_stock, reserved_stock, last_ledger_id, version_number, updated_at)
                    VALUES (:tenant_id, :item_id, :cur, :res, :ledger_id, :new_ver, NOW())
                """), {
                    "tenant_id": self.tenant_id,
                    "item_id": catalog_item_id,
                    "cur": new_current,
                    "res": new_reserved,
                    "ledger_id": ledger_id,
                    "new_ver": new_version
                })

            # C. Emitir Evento tipado vía Outbox
            event_name = f"inventory.{movement_type.lower()}.v1"
            event_payload = InventoryMovementEventV1(
                event_id=str(uuid.uuid4()),
                correlation_id=correlation_id,
                tenant_id=str(self.tenant_id),
                timestamp=datetime.utcnow().isoformat() + "Z",
                source=source_type,
                catalog_item_id=str(catalog_item_id),
                movement_type=movement_type,
                reservation_type=reservation_type,
                reason_code=reason_code,
                quantity=quantity,
                new_available_stock=new_available,
                new_current_stock=new_current,
                new_reserved_stock=new_reserved,
                ledger_id=ledger_id
            ).model_dump(mode='json')

            tx.emit_event(
                event_type=event_name,
                aggregate_type="inventory_ledger",
                aggregate_id=ledger_id,
                payload=event_payload
            )

            # D. Audit Trail
            tx.set_audit_changes({
                "movement": movement_type,
                "delta": quantity,
                "correlation_id": correlation_id,
                "available_after": new_available
            })

        return ledger_id
