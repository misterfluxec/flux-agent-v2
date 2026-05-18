import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
import uuid

class MemoryAggregator:
    """
    Fase 4B — Sprint 4B.1 (Refined): Operational Memory Engine.

    Procesa el event_outbox en ventanas de tiempo y persiste snapshots
    inmutables (Time-Series) en tenant_memory_snapshots.
    Actualiza customer_memory_profiles con heurísticas extendidas.
    """

    WINDOW_CONFIGS = {
        "5min":   timedelta(minutes=5),
        "1h":     timedelta(hours=1),
        "24h":    timedelta(hours=24),
        "weekly": timedelta(days=7),
    }

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # ─────────────────────────────────────────────
    # TENANT PROFILE SNAPSHOTS (Time-Series)
    # ─────────────────────────────────────────────

    def aggregate_tenant_window(self, window_type: str = "1h") -> Dict[str, Any]:
        delta = self.WINDOW_CONFIGS.get(window_type, timedelta(hours=1))
        # Para ser deterministas, redondeamos la ventana actual a intervalos exactos
        now = datetime.now(timezone.utc)
        if window_type == "5min":
            window_end = now.replace(minute=now.minute - (now.minute % 5), second=0, microsecond=0)
        elif window_type == "1h":
            window_end = now.replace(minute=0, second=0, microsecond=0)
        else:
            window_end = now

        window_start = window_end - delta

        metrics = self._gather_tenant_metrics(window_start, window_end)
        operational_stability = self._compute_stability_score(metrics)
        risk_level = self._derive_risk_level(operational_stability)

        # Snapshot append-only (con idempotencia por si se repite en la misma ventana)
        upsert = text("""
            INSERT INTO tenant_memory_snapshots (
                id, tenant_id, aggregation_window, window_start, window_end,
                metrics_json, operational_stability, risk_level, computed_at
            ) VALUES (
                :id, :tenant_id, :window, :start, :end,
                :metrics_json, :stability, :risk, NOW()
            )
            ON CONFLICT (tenant_id, aggregation_window, window_start) DO UPDATE SET
                metrics_json = EXCLUDED.metrics_json,
                operational_stability = EXCLUDED.operational_stability,
                risk_level = EXCLUDED.risk_level,
                computed_at = NOW()
        """)

        self.db.execute(upsert, {
            "id": str(uuid.uuid4()),
            "tenant_id": self.tenant_id,
            "window": window_type,
            "start": window_start,
            "end": window_end,
            "metrics_json": json.dumps(metrics),
            "stability": operational_stability,
            "risk": risk_level
        })
        self.db.commit()

        return {"window_type": window_type, "operational_stability": operational_stability, "risk_level": risk_level}

    def _gather_tenant_metrics(self, start: datetime, end: datetime) -> Dict[str, Any]:
        """Calcula las métricas estructuradas para el JSON de la ventana."""
        q_pay = text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'paid')      AS paid_count,
                COUNT(*) FILTER (WHERE status = 'failed')    AS failed_count,
                COUNT(*) FILTER (WHERE status = 'chargeback') AS chargeback_count,
                AVG(CASE WHEN status = 'paid' THEN amount_cents / 100.0 END) AS avg_amount,
                SUM(CASE WHEN status = 'paid' THEN amount_cents / 100.0 ELSE 0 END) AS total_revenue
            FROM payment_intents
            WHERE tenant_id = :t AND created_at BETWEEN :s AND :e
        """)
        pay = self.db.execute(q_pay, {"t": self.tenant_id, "s": start, "e": end}).fetchone()
        
        total_pay = (pay.paid_count or 0) + (pay.failed_count or 0)
        payment_success_rate = (pay.paid_count / total_pay * 100) if total_pay else 100.0

        q_dlq = text("""
            SELECT
                COUNT(*) FILTER (WHERE status = 'dlq')        AS dlq_count,
                COUNT(*) FILTER (WHERE retry_count > 0)       AS retried,
                COUNT(*) FILTER (WHERE status = 'processed' AND retry_count > 0) AS recovered
            FROM event_outbox
            WHERE tenant_id = :t AND created_at BETWEEN :s AND :e
        """)
        dlq = self.db.execute(q_dlq, {"t": self.tenant_id, "s": start, "e": end}).fetchone()
        retry_recovery_rate = (dlq.recovered / dlq.retried * 100) if dlq and dlq.retried else 100.0

        q_drift = text("""
            SELECT COUNT(*) AS drift_count
            FROM event_outbox
            WHERE tenant_id = :t AND event_type = 'inventory.drift_detected.v1'
              AND created_at BETWEEN :s AND :e
        """)
        drift = self.db.execute(q_drift, {"t": self.tenant_id, "s": start, "e": end}).fetchone()

        q_orders = text("""
            SELECT COUNT(*) AS orders_count
            FROM orders
            WHERE tenant_id = :t AND created_at BETWEEN :s AND :e
        """)
        orders = self.db.execute(q_orders, {"t": self.tenant_id, "s": start, "e": end}).fetchone()
        orders_count = orders.orders_count if orders else 0
        
        # Opcional: Para nuevos clientes, si existe la tabla customers
        # Por ahora lo dejamos en 0 para no romper si no está creada, o hacemos un try-except.
        new_customers_count = 0
        
        revenue = float(pay.total_revenue or 0.0)
        avg_ticket = float(pay.avg_amount or 0.0)

        return {
            "business": {
                "revenue": round(revenue, 2),
                "orders_count": orders_count,
                "new_customers": new_customers_count,
                "avg_ticket": round(avg_ticket, 2)
            },
            "payment": {
                "success_rate": round(payment_success_rate, 2),
                "failure_rate": round(100.0 - payment_success_rate, 2),
                "avg_amount": round(avg_ticket, 2),
                "chargeback_count": pay.chargeback_count or 0,
            },
            "delivery": {
                "total_retries": dlq.retried if dlq else 0,
                "dlq_events": dlq.dlq_count if dlq else 0,
                "retry_recovery_rate": round(retry_recovery_rate, 2),
            },
            "inventory": {
                "drift_events": drift.drift_count if drift else 0,
            },
            "connectors": {
                "sync_success_rate": 100.0,
                "failures": 0,
                "schema_changes": 0
            }
        }

    def _compute_stability_score(self, m: Dict) -> float:
        score = 100.0
        score -= m["payment"]["failure_rate"] * 0.40
        score -= m["inventory"]["drift_events"] * 10.0
        score -= m["delivery"]["dlq_events"] * 5.0
        score -= (100.0 - m["delivery"]["retry_recovery_rate"]) * 0.10
        return round(max(score, 0.0), 2)

    def _derive_risk_level(self, score: float) -> str:
        if score >= 95: return "LOW"
        if score >= 80: return "MEDIUM"
        if score >= 60: return "HIGH"
        return "CRITICAL"

    # ─────────────────────────────────────────────
    # CUSTOMER PROFILE (Extended)
    # ─────────────────────────────────────────────

    def update_customer_profile(self, customer_id: str) -> Dict[str, Any]:
        """Actualiza el Customer Memory Profile con heurísticas de soporte y riesgo."""
        q = text("""
            SELECT
                COUNT(o.id)                              AS total_orders,
                SUM(o.total_amount)                      AS total_ltv,
                AVG(o.total_amount)                      AS avg_order_value,
                MAX(o.created_at)                        AS last_order_at,
                COUNT(pi.id) FILTER (WHERE pi.status = 'failed') AS total_failed_payments,
                COUNT(pi.id) FILTER (WHERE pi.status = 'failed' AND pi.created_at >= NOW() - INTERVAL '30 DAYS') AS failed_payments_30d
            FROM orders o
            LEFT JOIN payment_intents pi ON pi.order_id = o.id
            WHERE o.customer_id = :cid AND o.tenant_id = :t
        """)
        r = self.db.execute(q, {"cid": customer_id, "t": self.tenant_id}).fetchone()
        if not r: return {}

        total_orders = r.total_orders or 0
        failed_30d   = r.failed_payments_30d or 0
        total_failed = r.total_failed_payments or 0

        # Base scores
        churn_risk = min(0.0 + (0.3 if failed_30d >= 2 else 0.0) + (0.2 if total_orders < 3 else 0.0), 1.0)
        pay_reliability = max(1.0 - (failed_30d * 0.15), 0.0)
        health_score = round((pay_reliability * 0.6 + (1 - churn_risk) * 0.4) * 100, 2)
        risk_level = self._derive_risk_level(health_score)

        # Extended fields: Support Load & Operational Risk
        # Si un cliente tiene muchos fallos históricos, genera carga de soporte.
        support_load = min((total_failed * 0.2) + (1.0 if churn_risk > 0.7 else 0.0), 1.0)
        
        upsert = text("""
            INSERT INTO customer_memory_profiles (
                id, customer_id, tenant_id,
                churn_risk_score, payment_reliability_score,
                total_orders, total_ltv, failed_payments_30d,
                avg_order_value, last_order_at,
                operational_health_score, risk_level,
                operational_risk_level, support_load_score,
                last_computed_at
            ) VALUES (
                gen_random_uuid(), :cid, :t,
                :churn_risk, :pay_reliability,
                :total_orders, :total_ltv, :failed_30d,
                :avg_order_value, :last_order_at,
                :health_score, :risk_level,
                :op_risk, :support_load,
                NOW()
            )
            ON CONFLICT (customer_id, tenant_id) DO UPDATE SET
                churn_risk_score          = EXCLUDED.churn_risk_score,
                payment_reliability_score = EXCLUDED.payment_reliability_score,
                total_orders              = EXCLUDED.total_orders,
                total_ltv                 = EXCLUDED.total_ltv,
                failed_payments_30d       = EXCLUDED.failed_payments_30d,
                avg_order_value           = EXCLUDED.avg_order_value,
                last_order_at             = EXCLUDED.last_order_at,
                operational_health_score  = EXCLUDED.operational_health_score,
                risk_level                = EXCLUDED.risk_level,
                operational_risk_level    = EXCLUDED.operational_risk_level,
                support_load_score        = EXCLUDED.support_load_score,
                last_computed_at          = NOW()
        """)
        self.db.execute(upsert, {
            "cid":            customer_id,
            "t":              self.tenant_id,
            "churn_risk":     churn_risk,
            "pay_reliability": pay_reliability,
            "total_orders":   total_orders,
            "total_ltv":      float(r.total_ltv or 0),
            "failed_30d":     failed_30d,
            "avg_order_value": float(r.avg_order_value or 0),
            "last_order_at":  r.last_order_at,
            "health_score":   health_score,
            "risk_level":     risk_level,
            "op_risk":        risk_level, # Por ahora igual, se puede desvincular luego
            "support_load":   round(support_load, 4),
        })
        self.db.commit()

        return {
            "customer_id": customer_id, 
            "health_score": health_score, 
            "support_load": round(support_load, 4),
            "op_risk": risk_level
        }
