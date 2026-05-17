import uuid
from typing import Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from database import SesionLocal
from services.commerce_transaction_manager import CommerceTransactionManager
from domain.commerce_states import CommerceStateValidator, PaymentStatus
from domain.events.payment_events import PaymentStatusUpdatedEventV1

class PaymentReconciliationEngine:
    """
    Motor de Conciliación de Pagos (Sprint 3D.2).
    Lee eventos de webhook_events de forma segura (FOR UPDATE SKIP LOCKED),
    y aplica la lógica de transición de status en las órdenes y payment_intents,
    generando los eventos de dominio correctos.
    """

    async def process_pending_webhooks(self, batch_size: int = 50):
        async with SesionLocal() as db:
            query = text("""
                SELECT id, tenant_id, provider, provider_event_id, event_type, payload
                FROM webhook_events
                WHERE status = 'pending'
                ORDER BY created_at ASC
                LIMIT :limit
                FOR UPDATE SKIP LOCKED
            """)
            result = await db.execute(query, {"limit": batch_size})
            events = result.fetchall()

            count = 0
            for evt in events:
                try:
                    await self._process_single_webhook(db, str(evt.tenant_id), evt)
                    
                    await db.execute(text("UPDATE webhook_events SET status = 'processed', processed_at = NOW() WHERE id = :id"), 
                               {"id": evt.id})
                    await db.commit()
                    count += 1
                except Exception as e:
                    await db.rollback()
                    await db.execute(text("UPDATE webhook_events SET status = 'failed', error_message = :err WHERE id = :id"), 
                               {"id": evt.id, "err": str(e)})
                    await db.commit()
            return count

    async def _process_single_webhook(self, db: AsyncSession, tenant_id: str, webhook_event: Any):
        """
        Interpreta el payload del webhook y actualiza payment_intents y orders.
        """
        payload = webhook_event.payload
        provider = webhook_event.provider

        # --- Lógica de Mapeo de MercadoPago (Ejemplo Simplificado) ---
        # Asumimos que payload trae {"external_transaction_id": "12345", "status": "approved"}
        ext_txn_id = payload.get("external_transaction_id")
        raw_status = payload.get("status")

        if not ext_txn_id:
            raise ValueError("Webhook missing external_transaction_id")

        # Mapeo a dominio interno
        new_status: PaymentStatus = 'pending'
        if raw_status == 'approved':
            new_status = 'paid'
        elif raw_status == 'rejected':
            new_status = 'failed'
        
        # Buscar el Payment Intent original
        pi_query = text("""
            SELECT id, order_id, status, amount 
            FROM payment_intents 
            WHERE tenant_id = :tenant_id AND external_transaction_id = :ext_id
            FOR UPDATE
        """)
        result = await db.execute(pi_query, {"tenant_id": tenant_id, "ext_id": ext_txn_id})
        pi = result.fetchone()

        if not pi:
            # Quizá el intent se buscaba por idempotency_key o creamos un "Unlinked Payment"
            raise ValueError(f"Payment Intent for {ext_txn_id} not found.")

        current_status = pi.status
        if current_status == new_status:
            return # Ya procesado, idempotencia lógica superada

        CommerceStateValidator.validate_payment_transition(current_status, new_status)

        # Transacción Comercial Atómica
        tx_manager = CommerceTransactionManager(db, tenant_id)
        
        async with tx_manager.atomic_transaction(
            action_name="payment.reconciled",
            actor_type="webhook",
            actor_id=f"{provider}_{webhook_event.provider_event_id}",
            target_resource="payment_intent",
            target_id=pi.id
        ) as tx:

            # 1. Update Payment Intent
            await db.execute(text("UPDATE payment_intents SET status = :status, updated_at = NOW() WHERE id = :id"),
                       {"status": new_status, "id": pi.id})

            # 2. Update Order (Sincronización del status)
            await db.execute(text("UPDATE orders SET payment_status = :status WHERE id = :order_id"),
                       {"status": new_status, "order_id": pi.order_id})

            # 3. Emitir Eventos
            evt = PaymentStatusUpdatedEventV1(
                event_id=str(uuid.uuid4()),
                correlation_id=str(pi.order_id),
                tenant_id=tenant_id,
                timestamp=datetime.utcnow().isoformat() + "Z",
                source=provider,
                payment_intent_id=str(pi.id),
                order_id=str(pi.order_id),
                provider=provider,
                external_transaction_id=ext_txn_id,
                previous_status=current_status,
                new_status=new_status,
                amount=pi.amount
            )

            tx.emit_event(
                event_type=f"payment.{new_status}.v1",
                aggregate_type="payment_intent",
                aggregate_id=str(pi.id),
                payload=evt.model_dump(mode='json')
            )

            tx.set_audit_changes({
                "previous_status": current_status,
                "new_status": new_status,
                "external_txn": ext_txn_id
            })

            # INTEGRACION SPRINT 3D.3 (Conexión Inventory)
            # Si se pagó, podríamos enganchar la lógica de convertir la Reserva Soft a Hard aquí,
            # pero arquitectónicamente es mejor que otro micro-worker escuche `payment.paid.v1` 
            # y llame al ReservationEngine.commit_reservation().
