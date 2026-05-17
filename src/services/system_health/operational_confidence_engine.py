from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any

class OperationalConfidenceEngine:
    """
    Operational Confidence Engine v2.0 (Fase 4A Refinement).
    Score multidimensional que agrega la salud real de todos los dominios del sistema.
    Cada dimensión es independiente y ponderada estratégicamente.
    """
    def __init__(self, db: Session, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    def _payment_integrity_score(self) -> float:
        """Éxito de pagos + fiabilidad de webhooks (últimas 24h)"""
        # Payment success rate (60% del subtotal)
        q_pay = text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as successful
            FROM payment_intents
            WHERE tenant_id = :t AND created_at >= NOW() - INTERVAL '24 HOURS'
            AND status IN ('paid', 'failed', 'chargeback', 'refunded')
        """)
        r = self.db.execute(q_pay, {"t": self.tenant_id}).fetchone()
        payment_rate = (r.successful / r.total * 100) if r and r.total else 100.0

        # Webhook reliability (40% del subtotal)
        q_wh = text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'processed' THEN 1 ELSE 0 END) as processed
            FROM webhook_events
            WHERE tenant_id = :t AND created_at >= NOW() - INTERVAL '24 HOURS'
            AND status != 'pending'
        """)
        rw = self.db.execute(q_wh, {"t": self.tenant_id}).fetchone()
        webhook_rate = (rw.processed / rw.total * 100) if rw and rw.total else 100.0

        return (payment_rate * 0.6) + (webhook_rate * 0.4)

    def _inventory_integrity_score(self) -> float:
        """Salud del inventario: drifts activos degradan el score"""
        q = text("""
            SELECT COUNT(*) as active_drifts
            FROM event_outbox
            WHERE tenant_id = :t
              AND event_type = 'inventory.drift_detected.v1'
              AND status IN ('pending', 'dlq')
              AND created_at >= NOW() - INTERVAL '24 HOURS'
        """)
        try:
            r = self.db.execute(q, {"t": self.tenant_id}).fetchone()
            drifts = r.active_drifts if r else 0
            # Cada drift is_active resta 25 puntos, mínimo 0
            return max(100.0 - (drifts * 25.0), 0.0)
        except Exception:
            return 100.0

    def _connector_reliability_score(self) -> float:
        """Uptime y throughput de los conectores (sync jobs)"""
        q = text("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed
            FROM sync_jobs
            WHERE tenant_id = :t AND started_at >= NOW() - INTERVAL '24 HOURS'
        """)
        try:
            r = self.db.execute(q, {"t": self.tenant_id}).fetchone()
            return (r.completed / r.total * 100) if r and r.total else 100.0
        except Exception:
            return 100.0

    def _event_delivery_health_score(self) -> float:
        """Presión de la DLQ: muchos eventos muertos = sistema frágil"""
        q = text("""
            SELECT COUNT(*) as dlq_count
            FROM event_outbox
            WHERE tenant_id = :t AND status = 'dlq'
              AND created_at >= NOW() - INTERVAL '24 HOURS'
        """)
        try:
            r = self.db.execute(q, {"t": self.tenant_id}).fetchone()
            dlq = r.dlq_count if r else 0
            # 1-2 eventos DLQ = warning; 5+ = crítico
            if dlq == 0:   return 100.0
            if dlq <= 2:   return 85.0
            if dlq <= 5:   return 65.0
            return 40.0
        except Exception:
            return 100.0

    def _reconciliation_health_score(self) -> float:
        """Snapshots consistentes vs. reconstrucciones recientes"""
        q = text("""
            SELECT COUNT(*) as rebuilds
            FROM event_outbox
            WHERE tenant_id = :t
              AND event_type = 'inventory.snapshot_rebuilt.v1'
              AND created_at >= NOW() - INTERVAL '24 HOURS'
        """)
        try:
            r = self.db.execute(q, {"t": self.tenant_id}).fetchone()
            rebuilds = r.rebuilds if r else 0
            return max(100.0 - (rebuilds * 10.0), 70.0)
        except Exception:
            return 100.0

    def get_operational_confidence_score(self) -> Dict[str, Any]:
        """
        Operational Confidence Score v2.0 — Multidimensional.
        Pesos estratégicos reflejan el impacto de negocio de cada dimensión.
        """
        dimensions = {
            "payment_integrity":      (self._payment_integrity_score(),      0.35),
            "inventory_integrity":    (self._inventory_integrity_score(),    0.25),
            "connector_reliability":  (self._connector_reliability_score(),  0.20),
            "event_delivery_health":  (self._event_delivery_health_score(),  0.12),
            "reconciliation_health":  (self._reconciliation_health_score(),  0.08),
        }

        global_score = sum(score * weight for score, weight in dimensions.values())

        return {
            "global_operational_confidence": round(global_score, 2),
            "status": (
                "HEALTHY"  if global_score >= 95.0 else
                "WARNING"  if global_score >= 80.0 else
                "CRITICAL"
            ),
            "dimensions": {
                name: {"score": round(score, 2), "weight": weight}
                for name, (score, weight) in dimensions.items()
            }
        }
