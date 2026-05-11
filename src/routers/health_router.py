from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import obtener_sesion
from auth import PayloadToken, get_usuario_actual
from services.health.operational_health import OperationalHealthEngine
from core.plan_manager import redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/health", tags=["health", "operations"])

health_engine = OperationalHealthEngine(redis_client)


@router.get("/operational")
async def get_operational_health(
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Reporte de salud operacional del tenant.
    Datos que alimentan el panel 'Mission Control' del Operations Dashboard.

    Retorna:
      - overall_status: Estado global (ok/warning/degraded/critical)
      - checks: Lista de cada indicador con su estado y mensaje
      - requires_attention: Solo los checks que necesitan acción inmediata
    """
    try:
        return await health_engine.get_health_report(
            db=db,
            tenant_id=str(usuario.tenant_id)
        )
    except Exception as e:
        logger.error(f"Error en operational health report para {usuario.tenant_id}: {e}")
        raise HTTPException(status_code=500, detail="Error generando reporte de salud operacional")
