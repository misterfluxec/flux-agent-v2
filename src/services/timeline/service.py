# =============================================================================
# FLUXAGENT V2 — UNIFIED TIMELINE SERVICE (SSOT)
# =============================================================================
# Fuente de verdad única para el historial de eventos (Operational Graph).
# Consolida: UnifiedTimeline, CustomerTimeline y IntelligenceEngine.
# =============================================================================

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from core.telemetry.logger import get_logger

logger = get_logger(__name__)

class TimelineService:
    """
    Servicio de línea de tiempo de grado industrial.
    Maneja la federación de eventos técnicos y semánticos.
    """
    
    EVENT_CATEGORIES: Dict[str, Dict[str, str]] = {
        "message.received":     {"category": "interaction",  "severity": "low"},
        "message.sent":         {"category": "interaction",  "severity": "low"},
        "lead.created":         {"category": "commerce",     "severity": "medium"},
        "payment.completed":    {"category": "commerce",     "severity": "critical"},
        "payment.failed":       {"category": "commerce",     "severity": "critical"},
        "order.created":        {"category": "commerce",     "severity": "high"},
        "tool.executed":        {"category": "automation",   "severity": "low"},
        "alert.ia_detected":    {"category": "ops",          "severity": "high"},
    }

    def __init__(self, redis_client=None):
        self.redis = redis_client

    async def get_timeline(
        self,
        db: AsyncSession,
        tenant_id: str,
        aggregate_type: Optional[str] = None,
        aggregate_id: Optional[str] = None,
        customer_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna una vista unificada de eventos. 
        Soporta filtrado por Entidad (Agregado) o por Cliente.
        """
        params: Dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}
        query_parts = ["WHERE tenant_id = :tenant_id"]

        if aggregate_type and aggregate_id:
            query_parts.append("AND aggregate_type = :aggregate_type AND aggregate_id = :aggregate_id")
            params.update({"aggregate_type": aggregate_type, "aggregate_id": aggregate_id})
        
        if customer_id:
            # Asumiendo que customer_id está en el payload o es un campo de la tabla
            query_parts.append("AND aggregate_id = :customer_id") # En este contexto customer_id es el id de la entidad
            params.update({"customer_id": customer_id})

        where_clause = " ".join(query_parts)
        
        # Consultar la tabla event_log (SSOT)
        query = text(f"""
            SELECT event_id, event_type, aggregate_type, aggregate_id, payload,
                   severity, business_impact, occurred_at, correlation_id
            FROM event_log
            {where_clause}
            ORDER BY occurred_at DESC
            LIMIT :limit
        """)

        result = await db.execute(query, params)
        events = []
        for row in result.fetchall():
            cat_info = self.EVENT_CATEGORIES.get(row.event_type, {"category": "system", "severity": "low"})
            events.append({
                "id": row.event_id,
                "timestamp": row.occurred_at.isoformat() if row.occurred_at else None,
                "category": cat_info["category"],
                "type": row.event_type,
                "severity": row.severity or cat_info["severity"],
                "summary": self._generate_summary(row.event_type, row.payload or {}),
                "aggregate": {"type": row.aggregate_type, "id": str(row.aggregate_id)},
                "correlation_id": str(row.correlation_id) if row.correlation_id else None
            })
        return events

    def _generate_summary(self, event_type: str, payload: dict) -> str:
        """Genera un resumen legible según el type de evento."""
        if event_type == "payment.completed":
            return f"Pago de ${payload.get('amount', 0)} vía {payload.get('method', 'desconocido')}"
        if event_type == "order.created":
            return f"Nueva sort_order #{payload.get('order_number', 'N/A')}"
        return f"Evento {event_type} registrado"

# Singleton
_service = None

def get_timeline_service(redis_client=None) -> TimelineService:
    global _service
    if _service is None:
        _service = TimelineService(redis_client)
    return _service
