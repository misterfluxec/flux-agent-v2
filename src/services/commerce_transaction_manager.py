import json
from typing import Any, Dict, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

class CommerceTransactionManager:
    """
    Gestor de Transacciones Enterprise para FluxAgent V2.
    Garantiza "Domain Transaction Boundaries":
    1. Ejecuta la lógica de negocio.
    2. Guarda el evento en el Outbox (garantizando entrega si Redis cae).
    3. Escribe el Audit Trail (Trazabilidad estricta).
    4. Hace COMMIT de todo atómicamente, o ROLLBACK total.
    """
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def _write_outbox(self, event_type: str, aggregate_type: str, aggregate_id: str, payload: Dict[str, Any]):
        """Escribe el evento en la tabla Outbox dentro de la misma transacción DB"""
        query = text("""
            INSERT INTO event_outbox 
            (tenant_id, event_type, aggregate_type, aggregate_id, payload, status)
            VALUES (:tenant_id, :event_type, :aggregate_type, :aggregate_id, :payload, 'pending')
        """)
        await self.db.execute(query, {
            "tenant_id": self.tenant_id,
            "event_type": event_type,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "payload": json.dumps(payload)
        })

    async def _write_audit(self, action: str, actor_type: str, actor_id: str, target_resource: str, target_id: str, changes: Dict[str, Any]):
        """Escribe el Audit Log operacional en la misma transacción"""
        query = text("""
            INSERT INTO operational_audit_log 
            (tenant_id, action, actor_type, actor_id, target_resource, target_id, changes)
            VALUES (:tenant_id, :action, :actor_type, :actor_id, :target_resource, :target_id, :changes)
        """)
        await self.db.execute(query, {
            "tenant_id": self.tenant_id,
            "action": action,
            "actor_type": actor_type,
            "actor_id": actor_id,
            "target_resource": target_resource,
            "target_id": target_id,
            "changes": json.dumps(changes)
        })

    @asynccontextmanager
    async def atomic_transaction(
        self,
        action_name: str,
        actor_type: str,
        actor_id: str,
        target_resource: str,
        target_id: str
    ):
        """
        Context manager que envuelve una operación comercial crítica.
        Uso:
            async with manager.atomic_transaction(action="order.created", ...) as tx:
                # 1. update order
                # 2. lock inventory
                tx.add_event("order.created", "order", order.id, order_data)
                tx.add_audit_changes({"status_before": "pending", "status_after": "confirmed"})
        """
        # Objeto de contexto inyectado al caller para acumular eventos y cambios de auditoría
        class TransactionContext:
            def __init__(self):
                self.events = []
                self.audit_changes = {}

            def emit_event(self, event_type: str, aggregate_type: str, aggregate_id: str, payload: Dict[str, Any]):
                self.events.append((event_type, aggregate_type, aggregate_id, payload))
            
            def set_audit_changes(self, changes: Dict[str, Any]):
                self.audit_changes = changes

        tx_context = TransactionContext()

        try:
            # CEDEMOS EL CONTROL AL BLOQUE DE NEGOCIO (Yield)
            yield tx_context

            # Si el bloque de negocio terminó sin excepciones, escribimos OUTBOX y AUDIT
            for evt in tx_context.events:
                await self._write_outbox(evt[0], evt[1], evt[2], evt[3])
            
            await self._write_audit(
                action=action_name,
                actor_type=actor_type,
                actor_id=actor_id,
                target_resource=target_resource,
                target_id=target_id,
                changes=tx_context.audit_changes
            )

            # Si todo está bien, COMMIT de DB (Incluye Negocio + Outbox + Audit)
            await self.db.commit()
            logger.info(f"Commerce Transaction '{action_name}' committed successfully for tenant {self.tenant_id}")

        except Exception as e:
            # Si ocurre CUALQUIER error de negocio o de DB, ROLLBACK total.
            await self.db.rollback()
            logger.error(f"Commerce Transaction '{action_name}' FAILED. Rollback executed. Error: {str(e)}")
            raise e
