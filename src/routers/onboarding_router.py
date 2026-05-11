from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import logging

from database import obtener_sesion
from sqlalchemy.ext.asyncio import AsyncSession
from services.onboarding_service import apply_business_profile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/onboarding", tags=["onboarding"])

class ProfileRequest(BaseModel):
    profile_key: str
    tenant_id: str  # En un sistema real esto vendría del token JWT (Dependencia get_tenant_actual)

@router.post("/apply-profile")
async def apply_profile_endpoint(
    request: ProfileRequest,
    db: AsyncSession = Depends(obtener_sesion)
):
    try:
        result = await apply_business_profile(request.tenant_id, request.profile_key, db)
        return result
    except ValueError as e:
        logger.error(f"Error en onboarding: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error interno en onboarding: {e}")
        raise HTTPException(status_code=500, detail="Error aplicando el perfil de negocio")
