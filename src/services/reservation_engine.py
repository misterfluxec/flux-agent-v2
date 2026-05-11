import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from database import SessionLocal
from services.inventory_engine import InventoryEngineV2
from domain.commerce_states import ReservationType

class ReservationEngine:
    """
    Motor de Reservas (Sprint 3C.2).
    Gestiona el ciclo de vida temporal del inventario retenido (Soft/Hard).
    """
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.inventory_engine = InventoryEngineV2(db, tenant_id)

    def create_reservation(
        self,
        catalog_item_id: str,
        quantity: int,
        correlation_id: str,
        reservation_type: ReservationType = 'soft',
        source_type: str = 'checkout',
        source_id: Optional[str] = None,
        actor_id: str = 'system'
    ) -> str:
        """
        Crea una reserva activa y registra el movimiento 'RESERVE' en el Ledger.
        """
        # 1. Obtener el timeout configurado por el Tenant
        policy_q = text("SELECT reservation_timeout_minutes FROM tenant_inventory_policies WHERE tenant_id = :tenant_id")
        policy = self.db.execute(policy_q, {"tenant_id": self.tenant_id}).fetchone()
        timeout_minutes = policy.reservation_timeout_minutes if policy else 15

        # 2. Registrar el movimiento en el Ledger a través del InventoryEngine (atómico)
        ledger_id = self.inventory_engine.record_movement(
            catalog_item_id=catalog_item_id,
            movement_type='RESERVE',
            reason_code='checkout_pending' if reservation_type == 'soft' else 'quote_conversion',
            quantity=quantity,
            correlation_id=correlation_id,
            source_type=source_type,
            source_id=source_id,
            actor_id=actor_id,
            reservation_type=reservation_type
        )

        # 3. Insertar el tracker en active_reservations
        # NOTA: InventoryEngine.record_movement ya hace commit por dentro en un bloque atómico.
        # Por simplicidad de diseño actual, hacemos el trackeo en un paso separado, pero idealmente
        # InventoryEngine debería aceptar hooks o deberíamos envolverlo.
        # Aquí, para evitar la complejidad de reescribir record_movement, lo abrimos y hacemos la inserción.
        reservation_id = str(uuid.uuid4())
        self.db.execute(text("""
            INSERT INTO active_reservations 
            (id, tenant_id, catalog_item_id, correlation_id, ledger_id, reservation_type, quantity, expires_at)
            VALUES (:id, :tenant_id, :item_id, :correlation_id, :ledger_id, :type, :qty, NOW() + interval ':mins minutes')
        """), {
            "id": reservation_id,
            "tenant_id": self.tenant_id,
            "item_id": catalog_item_id,
            "correlation_id": correlation_id,
            "ledger_id": ledger_id,
            "type": reservation_type,
            "qty": quantity,
            "mins": timeout_minutes
        })
        self.db.commit()

        return reservation_id

    def commit_reservation(self, correlation_id: str, actor_id: str = 'system'):
        """
        Convierte una reserva activa en COMMIT (venta firme).
        """
        res_q = text("""
            SELECT id, catalog_item_id, quantity, reservation_type 
            FROM active_reservations 
            WHERE tenant_id = :tenant_id AND correlation_id = :corr_id AND status = 'active'
            FOR UPDATE
        """)
        reservation = self.db.execute(res_q, {"tenant_id": self.tenant_id, "corr_id": correlation_id}).fetchone()

        if not reservation:
            return  # No hay reserva activa para este correlation_id

        # Registrar COMMIT en Ledger
        self.inventory_engine.record_movement(
            catalog_item_id=str(reservation.catalog_item_id),
            movement_type='COMMIT',
            reason_code='quote_conversion',
            quantity=reservation.quantity,
            correlation_id=correlation_id,
            source_type='payment_gateway',
            actor_id=actor_id,
            reservation_type='hard'
        )

        # Marcar como committed
        self.db.execute(text("UPDATE active_reservations SET status = 'committed', updated_at = NOW() WHERE id = :id"), 
                        {"id": reservation.id})
        self.db.commit()


class ReservationExpirationWorker:
    """
    Worker silencioso que barre `active_reservations` caducadas
    y las libera mediante `InventoryEngineV2`.
    """
    def run(self, batch_size: int = 100):
        with SessionLocal() as db:
            query = text("""
                SELECT id, tenant_id, catalog_item_id, correlation_id, quantity 
                FROM active_reservations
                WHERE status = 'active' AND expires_at < NOW()
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            """)
            expired = db.execute(query, {"limit": batch_size}).fetchall()

            count = 0
            for res in expired:
                engine = InventoryEngineV2(db, str(res.tenant_id))
                
                # 1. Liberar en Ledger
                try:
                    engine.record_movement(
                        catalog_item_id=str(res.catalog_item_id),
                        movement_type='RELEASE',
                        reason_code='abandoned_cart_cleanup',
                        quantity=res.quantity,
                        correlation_id=res.correlation_id,
                        source_type='expiration_worker',
                        actor_id='system',
                        reservation_type=None
                    )
                    
                    # 2. Marcar como released
                    db.execute(text("UPDATE active_reservations SET status = 'released', updated_at = NOW() WHERE id = :id"), 
                               {"id": res.id})
                    db.commit()
                    count += 1
                except Exception as e:
                    db.rollback()
                    # Loggear error, pero continuar con el siguiente
                    print(f"Failed to release reservation {res.id}: {e}")

            return count
