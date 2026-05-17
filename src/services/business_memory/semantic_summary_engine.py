from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List
from datetime import datetime, timezone
import json
import logging

logger = logging.getLogger(__name__)

class SemanticSummaryEngine:
    """
    Fase 4B — Sprint 4B.2 (Refined): Semantic Operational Summaries.

    Genera resúmenes deterministas para el negocio y los clientes,
    asegurando que cada resumen incluya un `summary_confidence` (0.0-1.0)
    y un `summary_source` (ej. 'heuristic_engine').
    
    Introduce el `Operational Narrative`, una historia ejecutiva sobre
    el status actual del negocio.
    """

    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    async def generate_tenant_summary(self, window_type: str = "24h") -> Dict[str, Any]:
        """
        Lee el último snapshot de memoria y genera un resumen estructurado con confianza.
        """
        q = text("""
            SELECT metrics_json, operational_stability, risk_level
            FROM tenant_memory_snapshots
            WHERE tenant_id = :t AND aggregation_window = :w
            ORDER BY window_start DESC
            LIMIT 1
        """)
        try:
            res = await self.db.execute(q, {"t": self.tenant_id, "w": window_type})
            r = res.fetchone()
        except Exception as e:
            await self.db.rollback()
            logger.warning(f"Error o tabla no existe en tenant_memory_snapshots: {e}")
            r = None

        if not r:
            return {
                "summary": "No operational memory available for this period.",
                "confidence": 1.0,
                "source": "heuristic_engine:empty",
                "narrative": "Awaiting initial aggregation cycle.",
                "operational_stability": 100.0,
                "risk_level": "LOW"
            }

        m = r.metrics_json if isinstance(r.metrics_json, dict) else json.loads(r.metrics_json)
        lines = []
        confidence = 0.90 # Base confidence for deterministic metrics

        # Payment analysis
        psr = m.get("payment", {}).get("success_rate", 100.0)
        if psr >= 99:
            lines.append(f"✅ Excellent payment performance ({psr:.1f}% success).")
        elif psr >= 95:
            lines.append(f"⚠️ Degraded payment performance ({psr:.1f}% success).")
            confidence -= 0.05
        else:
            lines.append(f"🚨 Critical payment issues ({psr:.1f}% success).")

        # Inventory analysis
        drift = m.get("inventory", {}).get("drift_events", 0)
        if drift > 0:
            lines.append(f"🚨 {drift} inventory drift event(s) detected. Integrity compromised.")
            confidence -= 0.10
        else:
            lines.append("✅ Inventory integrity confirmed.")

        # Overall
        stability = r.operational_stability
        lines.append(f"📊 Business Stability Score: {stability:.1f}% ({r.risk_level} risk).")

        # Business Metrics (Fase 5B)
        biz = m.get("business", {})
        rev = biz.get("revenue", 0.0)
        orders = biz.get("orders_count", 0)
        lines.append(f"💰 Revenue: ${rev:.2f} ({orders} orders).")

        return {
            "tenant_id": self.tenant_id,
            "window_type": window_type,
            "operational_stability": stability,
            "risk_level": r.risk_level,
            "summary": " | ".join(lines),
            "narrative": " ".join(lines),
            "confidence": round(confidence, 2),
            "source": "heuristic_engine:tenant_snapshot",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def generate_operational_narrative(self) -> Dict[str, Any]:
        """
        Operational Narrative: Combina el último snapshot y las anomalías activas
        para crear un 'Story' de alto nivel.
        Ej: "El negocio experimentó un aumento de fallos de pago..."
        """
        tenant_sum = await self.generate_tenant_summary("1h")
        
        # Consultamos anomalías recientes (en un entorno real usaríamos el AnomalyDetector aquí o tabla)
        # Aquí integramos un resumen compuesto determinista.
        narrative_parts = []
        stability = tenant_sum.get("operational_stability", 100.0)
        risk = tenant_sum.get("risk_level", "LOW")

        if risk == "CRITICAL":
            narrative_parts.append("El negocio está operando bajo condiciones de alto riesgo.")
        elif risk == "HIGH":
            narrative_parts.append("El negocio muestra señales de degradación operativa importante.")
        elif risk == "MEDIUM":
            narrative_parts.append("El negocio opera con fricción moderada.")
        else:
            narrative_parts.append("El negocio está operando nominalmente y sin fricción significativa.")

        # Añadimos contexto del resumen
        if "Critical payment issues" in tenant_sum.get("narrative", ""):
            narrative_parts.append("Se ha detectado una caída crítica en la tasa de aceptación de pagos, lo que sugiere problemas con la pasarela.")
        elif "Degraded payment" in tenant_sum.get("narrative", ""):
            narrative_parts.append("Existe un aumento inusual en fallos de pagos recientes.")
            
        if "inventory drift" in tenant_sum.get("narrative", ""):
            narrative_parts.append("Adicionalmente, el motor de integridad detectó discrepancias (drift) entre el carrito y el Ledger, lo cual requiere atención inmediata.")

        if stability >= 95:
            narrative_parts.append("No se detectan anomalías en el ciclo de inventario o entregas.")

        final_narrative = " ".join(narrative_parts)

        return {
            "narrative": final_narrative,
            "confidence": tenant_sum["confidence"],
            "source": "heuristic_engine:narrative_synthesizer",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

    def generate_customer_summary(self, customer_id: str) -> Dict[str, Any]:
        """Resumen semántico del cliente."""
        q = text("""
            SELECT
                cmp.churn_risk_score,
                cmp.payment_reliability_score,
                cmp.total_orders,
                cmp.failed_payments_30d,
                cmp.operational_health_score,
                cmp.risk_level,
                cmp.support_load_score
            FROM customer_memory_profiles cmp
            WHERE cmp.customer_id = :cid AND cmp.tenant_id = :t
        """)
        r = self.db.execute(q, {"cid": customer_id, "t": self.tenant_id}).fetchone()

        if not r:
            return {"summary": "No data", "confidence": 1.0, "source": "heuristic_engine:empty"}

        lines = []
        churn_pct = int((r.churn_risk_score or 0) * 100)
        support_pct = int((r.support_load_score or 0) * 100)

        if churn_pct >= 70:
            lines.append(f"⚠️ High churn risk ({churn_pct}%).")
        else:
            lines.append(f"✅ Low churn risk.")

        if support_pct >= 50:
            lines.append(f"🚨 High support load propensity ({support_pct}%). Likely to open tickets.")

        return {
            "customer_id": customer_id,
            "health_score": r.operational_health_score,
            "summary": " ".join(lines),
            "confidence": 0.85,
            "source": "heuristic_engine:customer_profile",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    async def generate_incident_summary(self, correlation_id: str) -> Dict[str, Any]:
        """Mock para Fase 4C - Sprint 4C.1"""
        return {
            "event_count": 0,
            "timeline_narrative": f"Timeline for {correlation_id} currently unavailable.",
        }
