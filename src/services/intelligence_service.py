# =============================================================================
# FLUXAGENT V2 — CUSTOMER INTELLIGENCE SERVICE
# =============================================================================
# Gestiona el cálculo de métricas, scoring de clientes y engagement.
# Reemplaza la implementación dispersa en CustomerIntelligenceEngine.
# =============================================================================

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.telemetry.logger import get_logger

logger = get_logger(__name__)

class IntelligenceService:
    """
    Servicio encargado de procesar la inteligencia de negocio sobre clientes.
    """
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def update_customer_metrics(self, customer_id: str, category: str):
        """
        Recalcula métricas (LTV, engagement, etc) basadas en la actividad.
        """
        if category == "commerce":
            await self._update_financial_metrics(customer_id)
        elif category == "interaction":
            await self._update_engagement_metrics(customer_id)

    async def _update_financial_metrics(self, customer_id: str):
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
