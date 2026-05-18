from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any

from database import get_db
# Asumiendo una dependencia de auth mockeada por ahora
def get_current_tenant_id() -> str:
    return "tnt_01hq8xx123"

from services.ai_copilot.incident_explainer import IncidentExplainer
from services.business_memory.semantic_summary_engine import SemanticSummaryEngine
from services.business_memory.anomaly_detector import AnomalyDetector
from services.ai_copilot.context_engine import ContextEngine

router = APIRouter(prefix="/api/v1/copilot", tags=["AI Copilot"])

# Fase 4C — Sprint 4C.2: AI Read-Only APIs
# INVARIANTE: Ninguno de estos endpoints ejecuta acciones sobre el dominio transaccional.

@router.get("/insight")
def get_tenant_insight(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Obtiene una recomendación a nivel negocio (Tenant) utilizando la memoria operacional.
    Retorna la firma uniforme de respuesta AI.
    """
    explainer = IncidentExplainer(db, tenant_id)
    return explainer.generate_tenant_insight()


@router.get("/dashboard")
async def get_intelligence_dashboard(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Agrega toda la información para el dashboard de Inteligencia en una sola llamada rápida.
    """
    semantic_engine = SemanticSummaryEngine(db, tenant_id)
    anomaly_detector = AnomalyDetector(db, tenant_id)
    
    tenant_summary = await semantic_engine.generate_tenant_summary("1h")
    operational_narrative = await semantic_engine.generate_operational_narrative()
    active_anomalies = await anomaly_detector.detect_all()
    
    # Retrieve AI Insight
    explainer = IncidentExplainer(db, tenant_id)
    ai_insight = await explainer.generate_tenant_insight()

    # Extraer business metrics del raw snapshot (lo generamos en tenant_summary)
    # tenant_summary retorna las metrics si modificamos SemanticSummaryEngine,
    # pero podemos hacer una query directa al snapshot aquí para sacarlas rápido.
    q = text("""
        SELECT metrics_json, operational_stability, risk_level
        FROM tenant_memory_snapshots
        WHERE tenant_id = :t AND aggregation_window = '1h'
        ORDER BY window_start DESC
        LIMIT 1
    """)
    try:
        res = await db.execute(q, {"t": tenant_id})
        r = res.fetchone()
    except Exception:
        await db.rollback()
        r = None
    business_metrics = {
        "revenue_24h": 0.0,
        "orders_24h": 0,
        "avg_ticket": 0.0,
        "new_customers_24h": 0
    }
    stability_score = 100.0
    risk_level = "LOW"
    
    if r:
        import json
        m = r.metrics_json if isinstance(r.metrics_json, dict) else json.loads(r.metrics_json)
        biz = m.get("business", {})
        business_metrics = {
            "revenue_24h": biz.get("revenue", 0.0),
            "orders_24h": biz.get("orders_count", 0),
            "avg_ticket": biz.get("avg_ticket", 0.0),
            "new_customers_24h": biz.get("new_customers", 0)
        }
        stability_score = float(r.operational_stability)
        risk_level = r.risk_level

    return {
        "narrative": {
            "text": operational_narrative.get("narrative", ""),
            "confidence": operational_narrative.get("confidence", 1.0),
            "source": operational_narrative.get("source", ""),
            "generated_at": operational_narrative.get("generated_at", "")
        },
        "stability": {
            "score": stability_score,
            "risk_level": risk_level,
            "trend": "up" if stability_score >= 90 else "down",
            "window": "1h"
        },
        "anomalies": active_anomalies,
        "ai_insight": ai_insight,
        "business_metrics": business_metrics
    }


@router.get("/explain/{correlation_id}")
async def explain_incident(
    correlation_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Genera una explicación auditable y paso a paso de un incidente.
    """
    explainer = IncidentExplainer(db, tenant_id)
    return await explainer.explain(correlation_id)


@router.post("/ask")
async def ask_copilot(
    query: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Endpoint para consultas libres (Bounded). 
    En Fase 4C, este endpoint solo devuelve contexto pre-construido 
    o un mensaje limitante si la query sale del scope operacional.
    """
    # Para la implementación real, aquí se inyectaría el query intent al ContextEngine,
    # el cual seleccionaría qué snapshots traer.
    # Por ahora, mapea a un insight genérico.
    explainer = IncidentExplainer(db, tenant_id)
    insight = await explainer.generate_tenant_insight()
    
    insight["response"] = f"Respuesta acotada a '{query}': " + insight["response"]
    return insight


class AIFeedbackRequest(BaseModel):
    score: str # "USEFUL", "INCORRECT", "INCOMPLETE"
    reason: str = None

@router.post("/feedback/{audit_log_id}")
async def submit_ai_feedback(
    audit_log_id: str,
    feedback: AIFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_current_tenant_id)
) -> Dict[str, Any]:
    """
    Registra feedback humano sobre una respuesta específica de la IA.
    Esencial para el AI Quality Evaluation Layer y futuro RLHF.
    """
    valid_scores = ["USEFUL", "INCORRECT", "INCOMPLETE"]
    if feedback.score not in valid_scores:
        raise HTTPException(status_code=400, detail="Invalid score")

    q = text("""
        UPDATE ai_response_audit_log
        SET operator_feedback = :score,
            feedback_reason = :reason,
            feedback_given_at = NOW()
        WHERE id = :id AND tenant_id = :tenant_id
        RETURNING id
    """)
    
    res = await db.execute(q, {
        "score": feedback.score,
        "reason": feedback.reason,
        "id": audit_log_id,
        "tenant_id": tenant_id
    })
    result = res.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Audit log not found")
        
    await db.commit()
    
    return {"status": "success", "message": "Feedback recorded for RLHF."}

