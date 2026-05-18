from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.business_memory.memory_aggregator import MemoryAggregator
from services.business_memory.semantic_summary_engine import SemanticSummaryEngine
from services.business_memory.anomaly_detector import AnomalyDetector

router = APIRouter(prefix="/api/v1/memory", tags=["business-memory"])


def get_tenant_id() -> str:
    # Placeholder — en producción extrae del JWT
    return "demo-tenant-001"


# ─────────────────────────────────────────────
# TENANT MEMORY
# ─────────────────────────────────────────────

@router.get("/tenant/{tenant_id}")
def get_tenant_memory(
    tenant_id: str,
    window: str = "24h",
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna el perfil de memoria operacional del tenant para la ventana indicada.
    Consumido por el Mission Control header y el futuro AI Copilot.
    """
    engine = SemanticSummaryEngine(db, tenant_id)
    return engine.generate_tenant_summary(window_type=window)


@router.post("/tenant/{tenant_id}/aggregate")
def trigger_tenant_aggregation(
    tenant_id: str,
    window: str = "1h",
    db: AsyncSession = Depends(get_db),
):
    """
    Fuerza una agregación de memoria del tenant para la ventana indicada.
    Útil para testing o sincronización manual. En producción lo hace un cron.
    """
    aggregator = MemoryAggregator(db, tenant_id)
    result = aggregator.aggregate_tenant_window(window_type=window)
    return {"status": "aggregated", **result}


@router.get("/tenant/{tenant_id}/narrative")
def get_operational_narrative(
    tenant_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Operational Narrative: La "historia" ejecutiva del status actual del negocio.
    Combina métricas de snapshots y anomalías recientes.
    """
    engine = SemanticSummaryEngine(db, tenant_id)
    return engine.generate_operational_narrative()


# ─────────────────────────────────────────────
# CUSTOMER MEMORY
# ─────────────────────────────────────────────

@router.get("/customer/{customer_id}")
def get_customer_memory(
    customer_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Customer Memory Profile: churn risk, health score, payment reliability.
    Base de contexto para el Customer 360° y el futuro AI Copilot.
    """
    engine = SemanticSummaryEngine(db, tenant_id)
    return engine.generate_customer_summary(customer_id)


@router.post("/customer/{customer_id}/refresh")
def refresh_customer_profile(
    customer_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Re-computa el Customer Memory Profile de forma síncrona.
    Para actualizaciones post-transacción o tests.
    """
    aggregator = MemoryAggregator(db, tenant_id)
    result = aggregator.update_customer_profile(customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found or no orders yet.")
    return {"status": "refreshed", **result}


# ─────────────────────────────────────────────
# ANOMALY DETECTION
# ─────────────────────────────────────────────

@router.get("/anomalies")
def get_anomalies(
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Feed de anomalías detectadas en tiempo real para el tenant actual.
    Alimenta el Operational Alerts layer del Mission Control.
    """
    detector = AnomalyDetector(db, tenant_id)
    anomalies = detector.detect_all()
    return {
        "count": len(anomalies),
        "anomalies": anomalies
    }


# ─────────────────────────────────────────────
# INCIDENT / CORRELATION EXPLORER
# ─────────────────────────────────────────────

@router.get("/correlation/{correlation_id}")
def get_correlation_summary(
    correlation_id: str,
    tenant_id: str = Depends(get_tenant_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Correlation Explorer: Muestra la narrativa semántica de todos los eventos
    asociados a un correlation_id. El contexto completo de un incidente en un vistazo.
    """
    engine = SemanticSummaryEngine(db, tenant_id)
    return engine.generate_incident_summary(correlation_id)
