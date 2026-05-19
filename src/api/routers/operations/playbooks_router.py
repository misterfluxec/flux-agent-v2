from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import obtener_sesion
from auth import PayloadToken, get_usuario_actual
from services.commercial_playbooks import CommercialPlaybookService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/playbooks", tags=["playbooks"])

@router.get("/{industry}/effective")
async def get_effective_playbook(
    industry: str,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Obtiene la configuración del playbook maestro para una industria específica.
    """
    try:
        # En un sistema real el tenant tiene su propio custom playbook,
        # Si no existe, clona el template maestro de la industria seleccionada
        playbook = await CommercialPlaybookService.get_or_create_playbook(
            tenant_id=usuario.tenant_id,
            industry=industry,
            db=db
        )
        
        if not playbook:
            raise HTTPException(status_code=404, detail=f"Playbook template for {industry} not found")
            
        # Ocultar campos internos para el response
        return {
            "personality": playbook.get("personality", {}),
            "commercial_strategy": playbook.get("commercial_strategy", {}),
            "workflows": playbook.get("workflows", []),
            "sla_rules": playbook.get("sla_rules", {}),
            "kpi_targets": playbook.get("kpi_targets", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching playbook for {industry}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching playbook")
