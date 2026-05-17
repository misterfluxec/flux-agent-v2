from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime
import json
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class UnifiedTimelineService:
    """
    Servicio de línea de tiempo unificada basado en Event Sourcing.

    Estrategia dual de lectura:
      - Redis Streams: eventos últimas ~1h (velocidad de lectura para la UI)
      - PostgreSQL (event_log): historial completo, fuente de verdad inmutable

    Deduplicación: Postgres sobrescribe Redis para el mismo event_id.
    Límite de timeline: 50 eventos ordenados por timestamp DESC.
    """

    # Categorización visual para el frontend. El frontend decide el ícono/color;
    # el backend solo provee category + severity como semántica neutral.
    EVENT_CATEGORIES: Dict[str, Dict[str, str]] = {
        "message.received":     {"category": "interaction",  "default_severity": "low"},
        "message.sent":         {"category": "interaction",  "default_severity": "low"},
        "lead.created":         {"category": "commerce",     "default_severity": "medium"},
        "lead.qualified":       {"category": "commerce",     "default_severity": "medium"},
        "quote.generated":      {"category": "commerce",     "default_severity": "medium"},
        "quote.accepted":       {"category": "commerce",     "default_severity": "high"},
        "quote.rejected":       {"category": "commerce",     "default_severity": "low"},
        "order.created":        {"category": "commerce",     "default_severity": "high"},
        "payment.completed":    {"category": "commerce",     "default_severity": "critical"},
        "payment.failed":       {"category": "commerce",     "default_severity": "critical"},
        "booking.confirmed":    {"category": "commerce",     "default_severity": "high"},
        "booking.cancelled":    {"category": "commerce",     "default_severity": "medium"},
        "handoff.requested":    {"category": "ops",          "default_severity": "high"},
        "handoff.completed":    {"category": "ops",          "default_severity": "low"},
        "followup.scheduled":   {"category": "automation",   "default_severity": "low"},
        "followup.sent":        {"category": "automation",   "default_severity": "low"},
        "alert.ia_detected":    {"category": "ops",          "default_severity": "high"},
        "billing.alert":        {"category": "billing",      "default_severity": "critical"},
        "tool.executed":        {"category": "automation",   "default_severity": "low"},
    }

    def __init__(self, redis_client):
        self.redis = redis_client

    # =========================================================================
    # Lectura desde fuentes
    # =========================================================================

    async def _fetch_from_postgres(
        self,
        db: AsyncSession,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Fuente de verdad: event_log inmutable en Postgres."""
        result = await db.execute(text("""
            SELECT event_id, event_type, payload, severity, business_impact,
                   occurred_at, correlation_id
            FROM event_log
            WHERE tenant_id = :tenant_id
              AND aggregate_type = :aggregate_type
              AND aggregate_id = :aggregate_id
            ORDER BY occurred_at DESC
            LIMIT :limit
        """), {
            "tenant_id": tenant_id,
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "limit": limit
        })

        events = []
        for row in result.fetchall():
            events.append({
                "id": row.event_id,
                "type": row.event_type,
                "timestamp": row.occurred_at.isoformat() if row.occurred_at else None,
                "payload": row.payload or {},
                "severity": row.severity,
                "business_impact": row.business_impact,
                "correlation_id": str(row.correlation_id) if row.correlation_id else None,
                "source": "postgres"
            })
        return events

    async def _fetch_from_redis(
        self,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Cache de realtime: Redis Stream con TTL de ~1h."""
        stream_key = f"timeline:{tenant_id}:{aggregate_type}:{aggregate_id}"
        try:
            raw = await self.redis.xrevrange(stream_key, count=limit)
            events = []
            for _redis_id, fields in raw:
                try:
                    events.append({
                        "id": fields.get(b"event_id", b"").decode(),
                        "type": fields.get(b"event_type", b"").decode(),
                        "timestamp": fields.get(b"timestamp", b"").decode(),
                        "payload": json.loads(fields.get(b"payload", b"{}").decode()),
                        "severity": fields.get(b"severity", b"low").decode(),
                        "business_impact": fields.get(b"business_impact", b"").decode() or None,
                        "correlation_id": fields.get(b"correlation_id", b"").decode() or None,
                        "source": "redis"
                    })
                except Exception as parse_err:
                    logger.warning(f"Error parseando evento Redis: {parse_err}")
            return events
        except Exception as e:
            logger.error(f"Redis Stream read error (timeline): {e}")
            return []

    # =========================================================================
    # Timeline pública
    # =========================================================================

    async def get_timeline(
        self,
        db: AsyncSession,
        tenant_id: str,
        aggregate_type: str,
        aggregate_id: str,
        realtime: bool = True,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Retorna la línea de tiempo unificada ordenada por timestamp DESC.
        Postgres siempre tiene precedencia sobre Redis para el mismo event_id.
        """
        pg_events = await self._fetch_from_postgres(db, tenant_id, aggregate_type, aggregate_id, limit)
        redis_events = (
            await self._fetch_from_redis(tenant_id, aggregate_type, aggregate_id)
            if realtime else []
        )

        # Deduplicar: Redis primero, Postgres sobreescribe (payload completo)
        seen: Dict[str, Dict] = {}
        for evt in redis_events:
            if evt["id"]:
                seen[evt["id"]] = evt
        for evt in pg_events:
            if evt["id"]:
                seen[evt["id"]] = evt  # Postgres wins

        # Enriquecer y ordenar
        timeline = []
        for evt in sorted(seen.values(), key=lambda x: x.get("timestamp") or "", reverse=True):
            category_info = self.EVENT_CATEGORIES.get(
                evt["type"],
                {"category": "system", "default_severity": "low"}
            )
            # Postgres severity tiene priority; sino usar el default del type de evento
            effective_severity = evt.get("severity") or category_info["default_severity"]

            timeline.append({
                "id": evt["id"],
                "timestamp": evt["timestamp"],
                "category": category_info["category"],
                "type": evt["type"],
                "severity": effective_severity,
                "business_impact": evt.get("business_impact"),
                "summary": self._summarize_payload(evt["type"], evt.get("payload", {})),
                "correlation_id": evt.get("correlation_id"),
                # payload_full omitido por defecto: lo pide el frontend si necesita
            })

        return timeline[:limit]

    async def get_tenant_timeline(
        self,
        db: AsyncSession,
        tenant_id: str,
        event_types: Optional[List[str]] = None,
        severity_filter: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Timeline global del tenant (todas las entidades).
        Útil para el Operations Dashboard principal.
        Soporta filtro por type de evento y por severidad mínima.
        """
        severity_order = {"low": 0, "medium": 1, "high": 2, "critical": 3}
        min_sev = severity_order.get(severity_filter or "low", 0)

        # Construir filtro dinámico
        type_filter = ""
        params: Dict[str, Any] = {"tenant_id": tenant_id, "limit": limit}

        if event_types:
            type_filter = "AND event_type = ANY(:event_types)"
            params["event_types"] = event_types

        sev_filter_sql = ""
        if severity_filter:
            sev_filter_sql = "AND severity IN :severities"
            # Incluir la severidad pedida y las superiores
            allowed_sevs = tuple(k for k, v in severity_order.items() if v >= min_sev)
            params["severities"] = allowed_sevs

        result = await db.execute(text(f"""
            SELECT event_id, event_type, aggregate_type, aggregate_id, payload,
                   severity, business_impact, occurred_at, correlation_id
            FROM event_log
            WHERE tenant_id = :tenant_id
              {type_filter}
              {sev_filter_sql}
            ORDER BY occurred_at DESC
            LIMIT :limit
        """), params)

        timeline = []
        for row in result.fetchall():
            category_info = self.EVENT_CATEGORIES.get(
                row.event_type,
                {"category": "system", "default_severity": "low"}
            )
            timeline.append({
                "id": row.event_id,
                "timestamp": row.occurred_at.isoformat() if row.occurred_at else None,
                "category": category_info["category"],
                "type": row.event_type,
                "severity": row.severity or category_info["default_severity"],
                "business_impact": row.business_impact,
                "aggregate": {"type": row.aggregate_type, "id": str(row.aggregate_id)},
                "summary": self._summarize_payload(row.event_type, row.payload or {}),
                "correlation_id": str(row.correlation_id) if row.correlation_id else None,
            })

        return timeline

    # =========================================================================
    # Helpers
    # =========================================================================

    def _summarize_payload(self, event_type: str, payload: dict) -> str:
        """Resumen legible por humanos para la UI. Máx. 150 chars."""
        if not payload:
            return ""

        SUMMARIES = {
            "quote.generated": lambda p: f"Cotización ${p.get('total', 0):.2f} — {p.get('items_count', '?')} ítems",
            "quote.accepted":  lambda p: f"Aceptada por {p.get('customer_name', 'cliente')}",
            "payment.completed": lambda p: f"{p.get('method', 'pago')} • ${p.get('amount', 0):.2f}",
            "payment.failed":  lambda p: f"Fallo: {p.get('error_code', 'error')} — ${p.get('amount', 0):.2f}",
            "order.created":   lambda p: f"Orden #{p.get('order_number', '?')} — ${p.get('total', 0):.2f}",
            "booking.confirmed": lambda p: f"Reserva {p.get('date', '?')} — {p.get('service', '?')}",
            "message.received": lambda p: (p.get("content", "")[:100] + "...") if len(p.get("content", "")) > 100 else p.get("content", ""),
            "handoff.requested": lambda p: f"Handoff solicitado: {p.get('reason', 'sin razón')}",
        }

        summary_fn = SUMMARIES.get(event_type)
        if summary_fn:
            try:
                return summary_fn(payload)
            except Exception:
                pass

        return str(payload)[:150]
