from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, Dict, Any
from uuid import UUID
import json

from domain.customer_event_types import CustomerEventType, VisibilityLevel, CustomerEventCategory

class CustomerIntelligenceEngine:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id
        
    def _resolve_category(self, event_type: CustomerEventType) -> CustomerEventCategory:
        type_val = event_type.value
        if type_val.startswith("order.") or type_val.startswith("payment.") or type_val.startswith("quote."):
            return CustomerEventCategory.COMMERCE
        elif type_val.startswith("message.") or type_val.startswith("email.") or type_val.startswith("call."):
            return CustomerEventCategory.COMMUNICATION
        elif type_val.startswith("lead.") or type_val.startswith("appointment."):
            return CustomerEventCategory.SUPPORT
        return CustomerEventCategory.SYSTEM

    async def log_activity_event(
        self,
        customer_id: str,
        event_type: CustomerEventType,
        source_entity_type: str,
        source_entity_id: str,
        payload_snapshot: Dict[str, Any],
        schema_version: int = 1,
        correlation_id: Optional[str] = None,
        visibility_level: VisibilityLevel = VisibilityLevel.STANDARD,
        importance_score: int = 1,
        # Sprint G.7 Hardening args
        idempotency_key: Optional[str] = None,
        actor_type: str = "system",
        actor_id: Optional[str] = None,
        payload_version: str = "v1"
    ):
        """
        Inyecta un evento inmutable en el Activity Stream del cliente y en el Outbox.
        """
        category = self._resolve_category(event_type)
        
        # 1. Activity Stream
        query_activity = text("""
            INSERT INTO customer_activity_events (
                tenant_id, customer_id, event_type, event_category,
                source_entity_type, source_entity_id, 
                schema_version, payload_snapshot, 
                correlation_id, visibility_level, importance_score,
                idempotency_key, actor_type, actor_id
            ) VALUES (
                :tenant_id, :customer_id, :event_type, :event_category,
                :source_entity_type, :source_entity_id, 
                :schema_version, :payload_snapshot, 
                :correlation_id, :visibility_level, :importance_score,
                :idempotency_key, :actor_type, :actor_id
            ) RETURNING id
        """)
        
        res = await self.db.execute(query_activity, {
            "tenant_id": self.tenant_id,
            "customer_id": customer_id,
            "event_type": event_type.value,
            "event_category": category.value,
            "source_entity_type": source_entity_type,
            "source_entity_id": source_entity_id,
            "schema_version": schema_version,
            "payload_snapshot": json.dumps(payload_snapshot),
            "correlation_id": correlation_id,
            "visibility_level": visibility_level.value,
            "importance_score": importance_score,
            "idempotency_key": idempotency_key,
            "actor_type": actor_type,
            "actor_id": actor_id
        })
        event_id = res.scalar()
        
        # 2. Transactional Outbox
        outbox_payload = {
            "event_id": str(event_id),
            "customer_id": customer_id,
            "payload_snapshot": payload_snapshot
        }
        
        query_outbox = text("""
            INSERT INTO outbox_events (
                tenant_id, aggregate_id, event_type, payload_version, payload
            ) VALUES (
                :tenant_id, :aggregate_id, :event_type, :payload_version, :payload
            )
        """)
        
        await self.db.execute(query_outbox, {
            "tenant_id": self.tenant_id,
            "aggregate_id": customer_id,
            "event_type": event_type.value,
            "payload_version": payload_version,
            "payload": json.dumps(outbox_payload)
        })
        
        # 2. Actualizar Métricas de forma asíncrona (CACHÉ)
        if category == CustomerEventCategory.COMMERCE:
            await self._update_financial_metrics(customer_id)
        elif category == CustomerEventCategory.COMMUNICATION:
            await self._update_engagement_metrics(customer_id)

    async def _update_financial_metrics(self, customer_id: str):
        # Recalcular usando orders (que es más seguro) o eventos financieros
        # Por ahora lo mantenemos ligero basándonos en orders pagadas o confirmadas
        query = text("""
            UPDATE customer_metrics
            SET 
                order_count = (SELECT count(*) FROM orders WHERE customer_id = :cid AND tenant_id = :tid AND status != 'cancelled'),
                ltv = (SELECT COALESCE(sum(total_amount), 0) FROM orders WHERE customer_id = :cid AND tenant_id = :tid AND payment_status = 'paid'),
                last_purchase_at = (SELECT max(created_at) FROM orders WHERE customer_id = :cid AND tenant_id = :tid AND payment_status = 'paid'),
                updated_at = NOW()
            WHERE customer_id = :cid AND tenant_id = :tid
        """)
        await self.db.execute(query, {"cid": customer_id, "tid": self.tenant_id})
        
    async def _update_engagement_metrics(self, customer_id: str):
        query = text("""
            UPDATE customer_metrics
            SET 
                last_interaction_at = NOW(),
                updated_at = NOW()
            WHERE customer_id = :cid AND tenant_id = :tid
        """)
        await self.db.execute(query, {"cid": customer_id, "tid": self.tenant_id})

    async def get_customer_timeline(self, customer_id: str, limit: int = 50, offset: int = 0):
        """
        Recupera el historial operativo (Timeline) sin joins pesados.
        """
        query = text("""
            SELECT 
                id, event_type, event_category, event_timestamp, 
                source_entity_type, source_entity_id, 
                payload_snapshot, schema_version,
                visibility_level, importance_score
            FROM customer_activity_events
            WHERE tenant_id = :tenant_id AND customer_id = :customer_id
            ORDER BY event_timestamp DESC
            LIMIT :limit OFFSET :offset
        """)
        
        res = await self.db.execute(query, {
            "tenant_id": self.tenant_id, 
            "customer_id": customer_id,
            "limit": limit,
            "offset": offset
        })
        
        events = []
        for row in res.fetchall():
            payload = row.payload_snapshot
            if isinstance(payload, str):
                payload = json.loads(payload)
                
            events.append({
                "id": str(row.id),
                "type": row.event_type,
                "category": getattr(row, 'event_category', 'system'),
                "timestamp": row.event_timestamp.isoformat(),
                "source": {
                    "type": row.source_entity_type,
                    "id": str(row.source_entity_id) if row.source_entity_id else None
                },
                "payload": payload,
                "visibility": row.visibility_level,
                "importance": row.importance_score
            })
            
        return events
