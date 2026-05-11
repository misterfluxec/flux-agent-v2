from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from services.system_health.operational_confidence_engine import OperationalConfidenceEngine
from services.system_health.replay_engine import ReplayableEventsEngine

router = APIRouter(prefix="/api/v1/system", tags=["system-health"])


def get_tenant_id_header() -> str:
    # Placeholder — en producción se extrae del JWT
    return "demo-tenant-001"


@router.get("/health")
def get_system_health(
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id_header),
):
    """
    Endpoint principal del Mission Control.
    Retorna el Operational Confidence Score y las métricas de salud del sistema.
    Consumido por el frontend via React Query + polling o WebSocket patch.
    """
    engine = OperationalConfidenceEngine(db, tenant_id)
    return engine.get_operational_confidence_score()


@router.get("/dlq")
def get_dlq_events(
    limit: int = 50,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id_header),
):
    """
    Retorna los eventos en Dead Letter Queue para el DLQ & Retry Center.
    """
    replay = ReplayableEventsEngine(db, tenant_id)
    return {"events": replay.get_dlq_events(limit=limit)}


@router.post("/dlq/{event_id}/replay")
def replay_dlq_event(
    event_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id_header),
):
    """
    Re-encola un evento de la DLQ para reprocesamiento.
    Valida contra el EventRegistry que el evento tenga replayable=True.
    """
    replay = ReplayableEventsEngine(db, tenant_id)
    try:
        success = replay.replay_event(event_id)
        return {"status": "queued", "event_id": event_id}
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/dlq/{event_id}/archive")
def archive_dlq_event(
    event_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id_header),
):
    """
    Archiva un evento de la DLQ aplicando la retention policy correspondiente.
    """
    replay = ReplayableEventsEngine(db, tenant_id)
    replay.archive_dlq_event(event_id)
    return {"status": "archived", "event_id": event_id}
