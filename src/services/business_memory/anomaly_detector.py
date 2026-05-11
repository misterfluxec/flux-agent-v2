from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import List, Dict, Any
from datetime import datetime, timedelta, timezone

class AnomalyDetector:
    """
    Fase 4B — Sprint 4B.2 (Refined): Anomaly Intelligence Engine.

    Detecta comportamientos operacionales anómalos usando heurísticas,
    thresholds y moving averages. SIN ML todavía.
    
    Añadido:
    - Categorías: Volume, Integrity, Reliability, Financial, Behavioral.
    - anomaly_confidence (0.0-1.0)
    - impact_score (0-100)
    """

    THRESHOLDS = {
        "payment_failure_spike_pct":   15.0,
        "payment_failure_critical_pct": 30.0,
        "drift_events_per_hour":        2,
        "dlq_events_per_hour":          3,
        "retry_rate_spike_pct":         25.0,
    }

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def detect_all(self) -> List[Dict[str, Any]]:
        anomalies = []
        detectors = [
            self._detect_payment_failure_spike,
            self._detect_inventory_drift_frequency,
            self._detect_dlq_pressure,
            self._detect_retry_escalation,
        ]
        for detector in detectors:
            try:
                result = await detector()
                if result:
                    anomalies.append(result)
            except Exception as e:
                await self.db.rollback()
                import logging
                logging.getLogger(__name__).warning(f"Error en detector {detector.__name__}: {e}")
        return anomalies

    async def _detect_payment_failure_spike(self) -> Dict[str, Any] | None:
        q = text("""
            SELECT
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 HOUR')   AS recent_total,
                COUNT(*) FILTER (WHERE status = 'failed' AND created_at >= NOW() - INTERVAL '1 HOUR') AS recent_failed,
                COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 HOURS') AS baseline_total,
                COUNT(*) FILTER (WHERE status = 'failed' AND created_at >= NOW() - INTERVAL '24 HOURS') AS baseline_failed
            FROM payment_intents
            WHERE tenant_id = :t
        """)
        res = await self.db.execute(q, {"t": self.tenant_id})
        r = res.fetchone()
        if not r or not r.recent_total: return None

        recent_rate   = (r.recent_failed / r.recent_total * 100) if r.recent_total else 0.0
        baseline_rate = (r.baseline_failed / r.baseline_total * 100) if r.baseline_total else 0.0

        if recent_rate >= self.THRESHOLDS["payment_failure_critical_pct"]:
            severity = "CRITICAL"
            impact = 90
            conf = 0.95
        elif recent_rate >= self.THRESHOLDS["payment_failure_spike_pct"] and recent_rate > baseline_rate * 1.5:
            severity = "HIGH"
            impact = 75
            conf = 0.85
        else:
            return None

        return {
            "type": "PAYMENT_FAILURE_SPIKE",
            "category": "Financial",
            "severity": severity,
            "impact_score": impact,
            "anomaly_confidence": conf,
            "title": "Unusual Payment Failure Rate Detected",
            "description": f"Payment failure rate spiked to {recent_rate:.1f}% in the last hour.",
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _detect_inventory_drift_frequency(self) -> Dict[str, Any] | None:
        q = text("""
            SELECT COUNT(*) AS drift_count
            FROM event_outbox
            WHERE tenant_id = :t AND event_type = 'inventory.drift_detected.v1'
              AND created_at >= NOW() - INTERVAL '1 HOUR'
        """)
        res = await self.db.execute(q, {"t": self.tenant_id})
        r = res.fetchone()
        drift_count = r.drift_count if r else 0

        if drift_count < self.THRESHOLDS["drift_events_per_hour"]:
            return None

        return {
            "type": "INVENTORY_DRIFT_FREQUENCY",
            "category": "Integrity",
            "severity": "CRITICAL" if drift_count >= 5 else "HIGH",
            "impact_score": 85 if drift_count >= 5 else 60,
            "anomaly_confidence": 0.99, # Drift is a hard signal
            "title": "Repeated Inventory Drift Detected",
            "description": f"{drift_count} inventory drift events in the last hour.",
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _detect_dlq_pressure(self) -> Dict[str, Any] | None:
        q = text("""
            SELECT COUNT(*) AS dlq_count FROM event_outbox
            WHERE tenant_id = :t AND status = 'dlq' AND created_at >= NOW() - INTERVAL '1 HOUR'
        """)
        res = await self.db.execute(q, {"t": self.tenant_id})
        r = res.fetchone()
        dlq_count = r.dlq_count if r else 0

        if dlq_count < self.THRESHOLDS["dlq_events_per_hour"]: return None

        return {
            "type": "DLQ_PRESSURE",
            "category": "Reliability",
            "severity": "CRITICAL" if dlq_count >= 10 else "HIGH",
            "impact_score": 80 if dlq_count >= 10 else 55,
            "anomaly_confidence": 0.90,
            "title": "Dead Letter Queue Under Pressure",
            "description": f"{dlq_count} events moved to DLQ in the last hour.",
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }

    async def _detect_retry_escalation(self) -> Dict[str, Any] | None:
        q = text("""
            SELECT COUNT(*) AS total, COUNT(*) FILTER (WHERE retry_count >= 3) AS high_retries
            FROM event_outbox WHERE tenant_id = :t AND created_at >= NOW() - INTERVAL '1 HOUR'
        """)
        res = await self.db.execute(q, {"t": self.tenant_id})
        r = res.fetchone()
        if not r or not r.total: return None
        retry_rate = (r.high_retries / r.total * 100)

        if retry_rate < self.THRESHOLDS["retry_rate_spike_pct"]: return None

        return {
            "type": "RETRY_ESCALATION",
            "category": "Volume",
            "severity": "WARNING",
            "impact_score": 40,
            "anomaly_confidence": 0.80,
            "title": "Elevated Retry Rate Across Pipeline",
            "description": f"{retry_rate:.1f}% of events required 3+ retries.",
            "detected_at": datetime.now(timezone.utc).isoformat(),
        }
