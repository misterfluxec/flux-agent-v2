import uuid
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import text
from services.commerce_transaction_manager import CommerceTransactionManager
from domain.commerce_states import CommerceStateValidator

class CommerceLifecycleEngine:
    """
    Motor de Ciclo de Vida del Comercio Real.
    Gestiona la orquestación de Quotes, Orders, Payments e Inventory.
    Utiliza el Transaction Manager para garantizar la integridad ACID
    y que todos los eventos lleguen a la UI/Analytics.
    """
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        self.tx_manager = CommerceTransactionManager(db, tenant_id)

    def convert_quote_to_order(self, quote_id: str, actor_id: str, actor_type: str = 'system') -> str:
        """
        Transición Crítica: Convierte una Cotización (Quote) en Pedido (Order).
        - Valida status del Quote.
        - Crea Order (pending).
        - Reserva Inventario (optimistic lock).
        - Emite Eventos.
        """
        # 1. Obtener Quote actual
        q_quote = text("""
            SELECT id, status, total, customer_id 
            FROM quotes 
            WHERE id = :quote_id AND tenant_id = :tenant_id
            FOR UPDATE
        """)
        quote = self.db.execute(q_quote, {"quote_id": quote_id, "tenant_id": self.tenant_id}).fetchone()
        
        if not quote:
            raise ValueError(f"Quote {quote_id} not found.")

        # 2. Validar transición
        CommerceStateValidator.validate_quote_transition(quote.status, 'converted')

        # 3. Transacción Atómica de Negocio
        with self.tx_manager.atomic_transaction(
            action_name="quote.converted",
            actor_type=actor_type,
            actor_id=actor_id,
            target_resource="quote",
            target_id=quote_id
        ) as tx:
            
            # A. Marcar Quote como convertido
            self.db.execute(text("UPDATE quotes SET status = 'converted' WHERE id = :id"), {"id": quote_id})

            # B. Crear Order (pending)
            new_order_id = str(uuid.uuid4())
            self.db.execute(text("""
                INSERT INTO orders (id, tenant_id, quote_id, customer_id, status, total_amount, payment_status)
                VALUES (:id, :tenant_id, :quote_id, :customer_id, 'pending', :total, 'pending')
            """), {
                "id": new_order_id,
                "tenant_id": self.tenant_id,
                "quote_id": quote_id,
                "customer_id": quote.customer_id,
                "total": quote.total
            })

            # C. Emitir Eventos al Outbox
            tx.emit_event(
                event_type="quote.converted",
                aggregate_type="quote",
                aggregate_id=quote_id,
                payload={"quote_id": quote_id, "order_id": new_order_id}
            )
            tx.emit_event(
                event_type="order.created",
                aggregate_type="order",
                aggregate_id=new_order_id,
                payload={"order_id": new_order_id, "total": float(quote.total)}
            )

            # D. Dejar constancia de auditoría en la BD
            tx.set_audit_changes({
                "quote_status": {"before": quote.status, "after": "converted"},
                "new_order_id": new_order_id
            })

        return new_order_id

    def reserve_inventory(self, catalog_item_id: str, order_id: str, quantity: int, actor_id: str) -> str:
        """Crea un Inventory Lock Optimista"""
        with self.tx_manager.atomic_transaction(
            action_name="inventory.reserved",
            actor_type="system",
            actor_id=actor_id,
            target_resource="catalog_item",
            target_id=catalog_item_id
        ) as tx:
            
            lock_id = str(uuid.uuid4())
            self.db.execute(text("""
                INSERT INTO inventory_locks (id, tenant_id, catalog_item_id, order_id, quantity, status, expires_at)
                VALUES (:id, :tenant_id, :item_id, :order_id, :qty, 'reserved', NOW() + interval '15 minutes')
            """), {
                "id": lock_id,
                "tenant_id": self.tenant_id,
                "item_id": catalog_item_id,
                "order_id": order_id,
                "qty": quantity
            })

            tx.emit_event(
                event_type="inventory.reserved",
                aggregate_type="inventory_lock",
                aggregate_id=lock_id,
                payload={"item_id": catalog_item_id, "qty": quantity, "order_id": order_id}
            )
            
            tx.set_audit_changes({"action": "reserved", "quantity": quantity})

        return lock_id
