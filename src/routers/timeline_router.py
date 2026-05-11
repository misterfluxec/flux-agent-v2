from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import obtener_sesion
from auth import PayloadToken, get_usuario_actual
from services.timeline.unified_timeline import UnifiedTimelineService
from core.plan_manager import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/operations", tags=["operations", "timeline"])

timeline_service = UnifiedTimelineService(redis_client)


@router.get("/{aggregate_type}/{aggregate_id}/timeline")
async def get_entity_timeline(
    aggregate_type: str,
    aggregate_id: str,
    realtime: bool = Query(default=True, description="Incluir eventos de Redis Stream"),
    limit: int = Query(default=50, le=100, description="Número máximo de eventos"),
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Línea de tiempo de eventos para una entidad específica.
    Agregates soportados: 'lead', 'quote', 'order', 'booking'.
    """
    try:
        return await timeline_service.get_timeline(
            db=db,
            tenant_id=str(usuario.tenant_id),
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            realtime=realtime,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching timeline for {aggregate_type}/{aggregate_id}: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo timeline de la entidad")


@router.get("/timeline")
async def get_operations_dashboard_feed(
    event_types: Optional[str] = Query(default=None, description="Filtrar por tipos de evento separados por coma: 'payment.completed,quote.generated'"),
    severity: Optional[str] = Query(default=None, description="Severidad mínima: low|medium|high|critical"),
    limit: int = Query(default=50, le=100),
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Feed global de eventos del tenant para el Operations Dashboard.
    Soporte para filtros por tipo de evento y severidad mínima.
    Este es el endpoint que consume la vista 'Requieren Atención' y 'Todo'.
    """
    try:
        event_types_list: Optional[List[str]] = None
        if event_types:
            event_types_list = [e.strip() for e in event_types.split(",") if e.strip()]

        return await timeline_service.get_tenant_timeline(
            db=db,
            tenant_id=str(usuario.tenant_id),
            event_types=event_types_list,
            severity_filter=severity,
            limit=limit
        )
    except Exception as e:
        logger.error(f"Error fetching operations dashboard feed: {e}")
        raise HTTPException(status_code=500, detail="Error obteniendo feed operacional")
