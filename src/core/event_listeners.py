"""
Event Listener: Persiste eventos en la Unified Timeline.

Integra:
  - SeverityEngine: calcula severidad automáticamente antes de persistir
  - Correlation: propaga correlation_id del evento padre al contexto
  - Event Versioning: guarda event_version para compatibilidad histórica
  - Redis Stream: retention policy clara por type de tenant
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
import json
import logging
from typing import Dict, Any

from domain.events import DomainEvent
from core.severity_engine import SeverityEngine, SeverityContext
from core.correlation import propagate_from_event

logger = logging.getLogger(__name__)

# =============================================================================
# Redis Stream Retention Policy
# Clara, documentada, revisable.
# =============================================================================

# Máximo de entradas en el stream por entidad (FIFO trim automático)
# Esto protege memoria de Redis. El histórico completo siempre está en Postgres.
STREAM_MAXLEN_BY_PRIORITY = {
    "critical": 500,   # Eventos críticos: mantener más historia en Redis
    "high": 300,
    "medium": 200,
    "low": 100,        # Eventos de bajo impacto: rotar más rápido
}

# TTL del stream completo por entidad (segundos).
# Después de este tiempo sin nuevos eventos, el key expira de Redis.
# Postgres mantiene el histórico permanente.
STREAM_TTL_SEC = 3600 * 4  # 4 horas de ventana realtime


def _get_payload_dict(event: DomainEvent) -> Dict[str, Any]:
    """Extrae el payload como dict, guardando solo campos simples para Redis."""
    if hasattr(event.payload, "model_dump"):
        return event.payload.model_dump()
    if isinstance(event.payload, dict):
        return event.payload
    return {}


def _prune_payload_for_redis(payload: dict, max_bytes: int = 512) -> str:
    """
    Serializa el payload para Redis, truncando si supera max_bytes.
    Redis es cache de realtime, no storage — payloads grandes van a Postgres.
    """
    serialized = json.dumps(payload, ensure_ascii=False, default=str)
    if len(serialized.encode()) > max_bytes:
        # Guardamos solo campos de primer nivel (no listas ni dicts anidados)
        pruned = {k: v for k, v in payload.items() if not isinstance(v, (dict, list))}
        serialized = json.dumps(pruned, ensure_ascii=False, default=str)
    return serialized


async def persist_event_to_timeline(
    event: DomainEvent,
    db: AsyncSession,
    redis_conn: aioredis.Redis
):
    """
    Pipeline completo de persistencia de evento:
      1. Propagación de correlation (distributed tracing)
      2. Cálculo automático de severidad (SeverityEngine)
      3. Persistencia en Postgres (append-only, fuente de verdad)
      4. Push a Redis Stream (realtime cache con retention policy)
    """
    try:
        meta = event.metadata
        tenant_id = str(meta.tenant_id)
        aggregate_type = getattr(meta, "aggregate_type", "system")
        aggregate_id = getattr(meta, "aggregate_id", None)

        if not aggregate_id:
            return  # Sin entidad padre no hay timeline meaningful

        # ─────────────────────────────────────────────────────────────────────
        # 1. Correlation Tracing: propagar desde el evento padre
        # ─────────────────────────────────────────────────────────────────────
        propagate_from_event(
            parent_event_id=meta.event_id,
            parent_correlation_id=getattr(meta, "correlation_id", None)
        )

        correlation_id = getattr(meta, "correlation_id", None)
        causation_id = getattr(meta, "causation_id", None)

        # ─────────────────────────────────────────────────────────────────────
        # 2. Severity Engine: calcular automáticamente
        # ─────────────────────────────────────────────────────────────────────
        payload_dict = _get_payload_dict(event)

        # En el futuro el orquestador puede pasar SeverityContext enriquecido
        # (is_vip_customer, payment_amount, etc.). Por ahora usamos defaults.
        context = SeverityContext(
            payment_amount=payload_dict.get("amount") or payload_dict.get("total"),
        )

        auto_severity, auto_impact, auto_score, auto_tags = SeverityEngine.calculate(
            event_type=meta.event_type.value,
            payload=payload_dict,
            context=context,
        )

        # Si el evento ya trae severity explícita (raro pero posible), tomar la más alta
        from core.severity_engine import _max_sev
        explicit_severity = getattr(meta, "severity", "low")
        final_severity = _max_sev(explicit_severity, auto_severity)

        # business_impact: usar el del SeverityEngine (es el canónico)
        final_impact = auto_impact or getattr(meta, "business_impact", None)

        # Priority score: usar el auto-calculado (más rico en contexto)
        final_score = max(auto_score, getattr(meta, "priority_score", 0))

        # Tags: merger de auto-tags + tags del metadata del evento
        explicit_tags = list(getattr(meta, "tags", []))
        all_tags = list(dict.fromkeys(auto_tags + explicit_tags))  # dedup preservando sort_order

        # ─────────────────────────────────────────────────────────────────────
        # 3. Postgres: Append-only event log (fuente de verdad inmutable)
        # ─────────────────────────────────────────────────────────────────────
        event_version = getattr(meta, "event_version", 1)

        await db.execute(text("""
            INSERT INTO event_log (
                event_type, event_id, event_version, aggregate_type, aggregate_id,
                tenant_id, payload, severity, business_impact, priority_score, tags,
                occurred_at, correlation_id, causation_id
            ) VALUES (
                :event_type, :event_id, :event_version, :aggregate_type, :aggregate_id,
                :tenant_id, :payload, :severity, :business_impact, :priority_score, :tags,
                :occurred_at, :correlation_id, :causation_id
            )
            ON CONFLICT (tenant_id, event_id) DO NOTHING
        """), {
            "event_type":     meta.event_type.value,
            "event_id":       str(meta.event_id),
            "event_version":  event_version,
            "aggregate_type": aggregate_type,
            "aggregate_id":   str(aggregate_id),
            "tenant_id":      tenant_id,
            "payload":        json.dumps(payload_dict, default=str),
            "severity":       final_severity,
            "business_impact": final_impact,
            "priority_score": final_score,
            "tags":           all_tags,
            "occurred_at":    meta.timestamp,
            "correlation_id": str(correlation_id) if correlation_id else None,
            "causation_id":   str(causation_id) if causation_id else None,
        })
        await db.commit()

        # ─────────────────────────────────────────────────────────────────────
        # 4. Redis Stream: realtime cache con retention policy clara
        # ─────────────────────────────────────────────────────────────────────
        stream_key = f"timeline:{tenant_id}:{aggregate_type}:{aggregate_id}"
        maxlen = STREAM_MAXLEN_BY_PRIORITY.get(final_severity, 200)

        await redis_conn.xadd(stream_key, {
            "event_id":        str(meta.event_id),
            "event_type":      meta.event_type.value,
            "event_version":   str(event_version),
            "timestamp":       meta.timestamp.isoformat(),
            "payload":         _prune_payload_for_redis(payload_dict),
            "severity":        final_severity,
            "priority_score":  str(final_score),
            "tags":            json.dumps(all_tags),
            "business_impact": final_impact or "",
            "correlation_id":  str(correlation_id) if correlation_id else "",
            "causation_id":    str(causation_id) if causation_id else "",
        }, maxlen=maxlen, approximate=True)

        # TTL: si no llegan nuevos eventos en 4h, el key expira automáticamente
        await redis_conn.expire(stream_key, STREAM_TTL_SEC)

    except Exception as e:
        logger.error(f"Error persistiendo evento {getattr(event.metadata, 'event_type', '?')} en timeline: {e}")
        try:
            await db.rollback()
        except Exception:
            pass
