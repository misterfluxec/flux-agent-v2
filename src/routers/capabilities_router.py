from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from database import obtener_sesion
from auth import PayloadToken, get_usuario_actual
from core.plan_manager import PlanManager, redis_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/capabilities", tags=["capabilities"])

@router.get("/check")
async def check_capability_endpoint(
    quota_type: str,
    requested: int = 1,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """
    Verifica límite de capacidad, ya sea estática (feature) o mensual (cuota).
    """
    try:
        tenant_info = await PlanManager.verificar_acceso_tenant(usuario.tenant_id, db)
        limits = tenant_info.get("limits", {})
        
        # Mapping para mapear `quota_type` a keys guardadas en redis
        key = f"monthly_{quota_type}"
        limit = limits.get(key, 0)
        
        if limit == -1 or limit >= 99999:
            return {"allowed": True, "remaining": -1, "limit": -1, "source": "redis"}
            
        mes = PlanManager._current_month_str() if hasattr(PlanManager, "_current_month_str") else None
        if not mes:
            from datetime import datetime, timezone
            mes = datetime.now(tz=timezone.utc).strftime("%Y-%m")
            
        redis_key = f"usage:{usuario.tenant_id}:{mes}:{quota_type}"
        current = int(await redis_client.get(redis_key) or 0)
        remaining = max(0, limit - current)
        
        return {
            "allowed": current + requested <= limit,
            "remaining": remaining,
            "limit": limit,
            "source": "redis"
        }
        
    except Exception as e:
        logger.error(f"Error checking capability {quota_type}: {e}")
        raise HTTPException(status_code=500, detail="Error al verificar la cuota")
