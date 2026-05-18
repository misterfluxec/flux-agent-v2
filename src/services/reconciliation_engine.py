import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import SesionLocal
from services.commerce_transaction_manager import CommerceTransactionManager
from services.inventory_engine import InventoryEngineV2
from domain.events.inventory_events import InventorySnapshotRebuiltEventV1, InventoryDriftDetectedEventV1

class ReconciliationEngine:
    """
    Motor de Conciliación e Integridad de Inventario (Sprint 3C.3).
    Garantiza que la verdad absoluta (Ledger) y la caché operacional (Snapshot)
    se mantengan matemáticamente perfectas, y maneja colisiones con ERPs externos.
    """
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tx_manager = CommerceTransactionManager(db, tenant_id)

    async def rebuild_snapshot_from_ledger(self, catalog_item_id: str, reason: str, actor_id: str = 'system'):
        """
        Snapshot Rebuild Strategy.
        Regenera la caché de inventario (Snapshot) sumando desde CERO todos los 
        movimientos registrados en el Ledger Inmutable.
        """
        # 1. Obtener suma agregada desde el Ledger
        query = text("""
            SELECT 
                SUM(CASE 
                    WHEN movement_type IN ('IMPORT', 'RETURN', 'TRANSFER', 'ADJUSTMENT', 'SYNC_CORRECTION') THEN quantity
                    WHEN movement_type = 'COMMIT' THEN -quantity
                    WHEN movement_type = 'REFUND' THEN quantity
                    ELSE 0 
                END) as calculated_current,
                SUM(CASE 
                    WHEN movement_type = 'RESERVE' THEN quantity
                    WHEN movement_type IN ('COMMIT', 'RELEASE') THEN -quantity
                    ELSE 0 
                END) as calculated_reserved,
                MAX(id) as last_ledger_id
            FROM inventory_ledger
            WHERE tenant_id = :tenant_id AND catalog_item_id = :item_id
        """)
        ledger_sum_res = await self.db.execute(query, {"tenant_id": self.tenant_id, "item_id": catalog_item_id})
        ledger_sum = ledger_sum_res.fetchone()

        calc_current = ledger_sum.calculated_current or 0
        calc_reserved = ledger_sum.calculated_reserved or 0
        calc_available = calc_current - calc_reserved
        last_ledger = ledger_sum.last_ledger_id

        # 2. Bloquear y reemplazar el snapshot actual en una transacción
        async with self.tx_manager.atomic_transaction(
            action_name="inventory.snapshot_rebuilt",
            actor_type="system",
            actor_id=actor_id,
            target_resource="catalog_item",
            target_id=catalog_item_id
        ) as tx:

            # Seleccionar snapshot anterior para el evento
            snap_q = text("""
                SELECT available_stock, version_number 
                FROM inventory_snapshots 
                WHERE tenant_id = :tenant_id AND catalog_item_id = :item_id FOR UPDATE
            """)
            snap_before_res = await self.db.execute(snap_q, {"tenant_id": self.tenant_id, "item_id": catalog_item_id})
            snap_before = snap_before_res.fetchone()
            
            old_available = snap_before.available_stock if snap_before else 0
            new_version = (snap_before.version_number + 1) if snap_before else 1

            # UPSERT del nuevo snapshot calculado
            await self.db.execute(text("""
                INSERT INTO inventory_snapshots (tenant_id, catalog_item_id, current_stock, reserved_stock, last_ledger_id, version_number, updated_at)
                VALUES (:tenant_id, :item_id, :cur, :res, :ledger_id, :ver, NOW())
                ON CONFLICT ON CONSTRAINT unique_tenant_item_snapshot 
                DO UPDATE SET 
                    current_stock = EXCLUDED.current_stock,
                    reserved_stock = EXCLUDED.reserved_stock,
                    last_ledger_id = EXCLUDED.last_ledger_id,
                    version_number = EXCLUDED.version_number,
                    updated_at = NOW()
            """), {
                "tenant_id": self.tenant_id,
                "item_id": catalog_item_id,
                "cur": calc_current,
                "res": calc_reserved,
                "ledger_id": last_ledger,
                "ver": new_version
            })

            # 3. Emitir evento versionado de reconstrucción
            evt = InventorySnapshotRebuiltEventV1(
                event_id=str(uuid.uuid4()),
                correlation_id=f"rebuild_{uuid.uuid4().hex[:8]}",
                tenant_id=str(self.tenant_id),
                timestamp=datetime.utcnow().isoformat() + "Z",
                source="reconciliation_engine",
                catalog_item_id=str(catalog_item_id),
                previous_available_stock=old_available,
                rebuilt_available_stock=calc_available,
                reason=reason
            )

            tx.emit_event(
                event_type="inventory.snapshot_rebuilt.v1",
                aggregate_type="catalog_item",
                aggregate_id=catalog_item_id,
                payload=evt.model_dump(mode='json')
            )
            
            tx.set_audit_changes({"old_available": old_available, "new_available": calc_available, "reason": reason})

    async def reconcile_with_external_system(self, catalog_item_id: str, external_stock: int, correlation_id: str):
        """
        Aplica las Inventory Policies cuando un ERP o Excel informa un stock diferente.
        """
        # 1. Leer política del Tenant
        pol_q = text("SELECT reconciliation_policy FROM tenant_inventory_policies WHERE tenant_id = :tenant_id")
        policy_row_res = await self.db.execute(pol_q, {"tenant_id": self.tenant_id})
        policy_row = policy_row_res.fetchone()
        policy = policy_row.reconciliation_policy if policy_row else 'LOCAL_WINS'

        if policy == 'LOCAL_WINS':
            # Ignoramos el ERP. FluxAgent manda.
            return
            
        # Si ERP_WINS o MERGE, leemos el snapshot local
        snap_q = text("SELECT current_stock, reserved_stock FROM inventory_snapshots WHERE tenant_id = :t AND catalog_item_id = :i")
        snap_res = await self.db.execute(snap_q, {"t": self.tenant_id, "i": catalog_item_id})
        snap = snap_res.fetchone()
        local_current = snap.current_stock if snap else 0

        if policy == 'ERP_WINS':
            # Hacemos un SYNC_CORRECTION forzado para que el current_stock iguale al external_stock.
            delta = external_stock - local_current
            if delta != 0:
                engine = InventoryEngineV2(self.db, self.tenant_id)
                await engine.record_movement(
                    catalog_item_id=catalog_item_id,
                    movement_type='SYNC_CORRECTION',
                    reason_code='erp_sync',
                    quantity=delta,
                    correlation_id=correlation_id,
                    source_type='erp_reconciliation',
                    actor_id='system'
                )

class InventoryIntegrityValidator:
    """
    Worker en segundo plano que detecta "Drift" (Corrupción) entre Snapshots y Ledgers.
    """
    async def check_drift(self, catalog_item_id: str, db: AsyncSession, tenant_id: str):
        # 1. Suma del Ledger
        query = text("""
            SELECT SUM(CASE WHEN movement_type IN ('IMPORT','RETURN','TRANSFER','ADJUSTMENT','SYNC_CORRECTION') THEN quantity
                            WHEN movement_type = 'COMMIT' THEN -quantity
                            WHEN movement_type = 'REFUND' THEN quantity ELSE 0 END) as calc_curr,
                   SUM(CASE WHEN movement_type = 'RESERVE' THEN quantity
                            WHEN movement_type IN ('COMMIT','RELEASE') THEN -quantity ELSE 0 END) as calc_res
            FROM inventory_ledger
            WHERE tenant_id = :t AND catalog_item_id = :i
        """)
        ledger_res = await db.execute(query, {"t": tenant_id, "i": catalog_item_id})
        ledger = ledger_res.fetchone()
        ledger_avail = (ledger.calc_curr or 0) - (ledger.calc_res or 0)

        # 2. Suma del Snapshot
        snap_q = text("SELECT available_stock, version_number FROM inventory_snapshots WHERE tenant_id = :t AND catalog_item_id = :i")
        snap_res = await db.execute(snap_q, {"t": tenant_id, "i": catalog_item_id})
        snap = snap_res.fetchone()
        
        if not snap:
            return

        snapshot_avail = snap.available_stock
        drift = ledger_avail - snapshot_avail

        if drift != 0:
            # 3. Detectado Drift. Emitir Evento Crítico de Alarma vía Outbox (usando TxManager)
            tx_manager = CommerceTransactionManager(db, tenant_id)
            async with tx_manager.atomic_transaction("inventory.drift_detected", "system", "integrity_worker", "catalog_item", catalog_item_id) as tx:
                
                evt = InventoryDriftDetectedEventV1(
                    event_id=str(uuid.uuid4()),
                    correlation_id=f"drift_{uuid.uuid4().hex[:8]}",
                    tenant_id=str(tenant_id),
                    timestamp=datetime.utcnow().isoformat() + "Z",
                    source="integrity_worker",
                    catalog_item_id=catalog_item_id,
                    snapshot_available=snapshot_avail,
                    ledger_calculated_available=ledger_avail,
                    drift_quantity=drift,
                    snapshot_version_number=snap.version_number
                )
                
                tx.emit_event(
                    event_type="inventory.drift_detected.v1",
                    aggregate_type="catalog_item",
                    aggregate_id=catalog_item_id,
                    payload=evt.model_dump(mode='json')
                )
                
                tx.set_audit_changes({"drift_quantity": drift, "action": "drift_alarm_raised"})
