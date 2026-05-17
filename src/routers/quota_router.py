"""
FLUXAGENT V2 — QUOTA ROUTER
==============================
Endpoints REST para gestión de cuotas híbridas.

Tenant (self-service):
  GET  /api/v1/quota/my-config              → Ver cuotas y modo actual
  PUT  /api/v1/quota/byoa                   → Configurar credenciales BYOA
  POST /api/v1/quota/switch-mode            → Cambiar entre pool/hybrid/byoa
  POST /api/v1/quota/send-low-quota-alert   → Enviar alerta manual de cuota baja

Admin (super_admin):
  POST /api/v1/quota/admin/plans/{plan_id}/quotas    → Actualizar cuotas de un plan
  POST /api/v1/quota/admin/tenants/{id}/reset        → Reset manual de cuotas
  GET  /api/v1/quota/admin/tenants/{id}/config       → Ver config completa de un tenant
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_tenant_actual, solo_super_admin, get_usuario_actual
from database import obtener_sesion
from core.encryption import EncryptionService, mask_sensitive
from services.quota_notifier import build_quota_banner_data
from tasks.quota_reset import manual_reset_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/quota", tags=["Cuotas y Canales"])


# ---------------------------------------------------------------------------
# Schemas Pydantic
# ---------------------------------------------------------------------------

class BYOAConfigRequest(BaseModel):
    cloud_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    waba_id: Optional[str] = None
    evolution_url: Optional[str] = None
    evolution_api_key: Optional[str] = None
    admin_whatsapp_number: Optional[str] = None


class SwitchModeRequest(BaseModel):
    new_mode: str  # global_pool | byoa | hybrid


class PlanQuotaUpdateRequest(BaseModel):
    cloud_api_quota: Optional[int] = None
    evolution_api_quota: Optional[int] = None
    reset_period_days: Optional[int] = None


class ManualResetRequest(BaseModel):
    reason: str = "manual_override"


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

async def _get_tenant_row(tenant_id: UUID, db: AsyncSession) -> dict:
    """Obtiene la fila del tenant con join al plan para tener cuotas."""
    result = await db.execute(text("""
        SELECT
            t.id,
            t.plan,
            t.quota_mode,
            t.preferred_channel,
            t.auto_fallback_enabled,
            t.is_byoa_enabled,
            t.byoa_cloud_token,
            t.byoa_phone_number_id,
            t.byoa_waba_id,
            t.byoa_evolution_url,
            t.byoa_evolution_api_key,
            t.admin_whatsapp_number,
            t.used_cloud_api,
            t.used_evolution_api,
            t.last_quota_reset_at,
            t.quota_low_notified_at,
            COALESCE(p.cloud_api_quota, 200)     AS cloud_api_quota,
            COALESCE(p.evolution_api_quota, 300) AS evolution_api_quota,
            COALESCE(p.reset_period_days, 30)    AS reset_period_days,
            COALESCE(p.allow_fallback_to_text, true) AS allow_fallback_to_text
        FROM tenants t
        LEFT JOIN plans p ON t.plan = p.id
        WHERE t.id = :tid
    """), {"tid": str(tenant_id)})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tenant no encontrado")
    return dict(row._mapping)


# ---------------------------------------------------------------------------
# ENDPOINTS TENANT (self-service)
# ---------------------------------------------------------------------------

@router.get("/my-config")
async def get_my_quota_config(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Devuelve la configuración de cuotas y el status de consumo actual del tenant."""
    tenant = await _get_tenant_row(tenant_id, db)

    cloud_quota    = tenant["cloud_api_quota"]
    evo_quota      = tenant["evolution_api_quota"]
    used_cloud     = tenant["used_cloud_api"] or 0
    used_evo       = tenant["used_evolution_api"] or 0

    remaining_cloud = (cloud_quota - used_cloud) if cloud_quota != -1 else -1
    remaining_evo   = (evo_quota - used_evo)     if evo_quota   != -1 else -1

    # Calcular fecha de próximo reset
    from datetime import timedelta
    last_reset = tenant["last_quota_reset_at"]
    next_reset = (
        (last_reset + timedelta(days=tenant["reset_period_days"])).isoformat()
        if last_reset else None
    )

    return {
        "plan": tenant["plan"],
        "quota_mode": tenant["quota_mode"],
        "preferred_channel": tenant["preferred_channel"],
        "auto_fallback_enabled": tenant["auto_fallback_enabled"],
        "byoa": {
            "enabled": tenant["is_byoa_enabled"],
            "cloud_configured": bool(tenant["byoa_cloud_token"]),
            "evolution_configured": bool(tenant["byoa_evolution_url"]),
            # NUNCA exponer tokens reales, solo si está configurado
            "cloud_token_masked": (
                mask_sensitive(tenant["byoa_cloud_token"])
                if tenant["byoa_cloud_token"] else None
            ),
            "phone_number_id": tenant["byoa_phone_number_id"],
            "waba_id": tenant["byoa_waba_id"],
            "evolution_url": tenant["byoa_evolution_url"],
        },
        "usage": {
            "cloud_api": {"used": used_cloud, "limit": cloud_quota, "remaining": remaining_cloud},
            "evolution_api": {"used": used_evo, "limit": evo_quota, "remaining": remaining_evo},
        },
        "next_reset_at": next_reset,
        "alert": build_quota_banner_data(tenant),  # None o dict con datos del banner
    }


from core.sensitive_logger import log_safe, log_info_safe

@router.put("/byoa")
@log_safe
async def configure_byoa(
    body: BYOAConfigRequest,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Guarda o actualiza las credenciales BYOA del tenant."""
    updates = {}

    if body.cloud_token is not None:
        updates["byoa_cloud_token"]     = EncryptionService.encrypt(body.cloud_token)
        updates["byoa_phone_number_id"] = body.phone_number_id
        updates["byoa_waba_id"]         = body.waba_id

    if body.evolution_url is not None:
        updates["byoa_evolution_url"]     = body.evolution_url
        updates["byoa_evolution_api_key"] = (
            EncryptionService.encrypt(body.evolution_api_key)
            if body.evolution_api_key else None
        )

    if body.admin_whatsapp_number is not None:
        updates["admin_whatsapp_number"] = body.admin_whatsapp_number

    if not updates:
        raise HTTPException(status_code=400, detail="No se enviaron datos para actualizar")

    # Activar BYOA automáticamente si hay credenciales
    updates["is_byoa_enabled"] = True

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["tid"] = str(tenant_id)

    await db.execute(
        text(f"UPDATE tenants SET {set_clause} WHERE id = :tid"),
        updates
    )

    safe_token = body.cloud_token[:8] + "***" if body.cloud_token else None
    
    log_info_safe(
        "BYOA configuration updated",
        tenant_id=tenant_id,
        cloud_token_preview=safe_token,
        phone_number_id=body.phone_number_id
    )
    return {"status": "configured", "byoa_enabled": True}


@router.post("/switch-mode")
async def switch_quota_mode(
    body: SwitchModeRequest,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Cambia el modo de operación de cuotas del tenant."""
    valid_modes = ("global_pool", "byoa", "hybrid")
    if body.new_mode not in valid_modes:
        raise HTTPException(
            status_code=400,
            detail=f"Modo inválido. Opciones: {', '.join(valid_modes)}"
        )

    # Validar que BYOA/hybrid tienen credenciales configuradas
    if body.new_mode in ("byoa", "hybrid"):
        tenant = await _get_tenant_row(tenant_id, db)
        if not tenant.get("byoa_cloud_token") and not tenant.get("byoa_evolution_url"):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Para activar BYOA o Híbrido primero debes configurar "
                    "tus credenciales en PUT /api/v1/quota/byoa"
                )
            )

    await db.execute(
        text("UPDATE tenants SET quota_mode = :mode WHERE id = :tid"),
        {"mode": body.new_mode, "tid": str(tenant_id)}
    )

    logger.info("Tenant %s: modo de cuota cambiado a %s", tenant_id, body.new_mode)
    return {"status": "switched", "new_mode": body.new_mode}



@router.post("/send-low-quota-alert")
async def send_low_quota_alert(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """
    Envía manualmente una alerta de cuota baja al número de admin registrado.
    El frontend llama esto cuando el usuario hace clic en 'Enviar recordatorio'.
    """
    from services.quota_notifier import QuotaNotifier

    tenant = await _get_tenant_row(tenant_id, db)
    admin_number = tenant.get("admin_whatsapp_number")

    if not admin_number:
        raise HTTPException(
            status_code=422,
            detail=(
                "No hay número de WhatsApp de admin configurado. "
                "Agrégalo en la configuración BYOA."
            )
        )

    # Forzar envío (ignorar la bandera de ya-notificado para alertas manuales)
    try:
        await QuotaNotifier._send_whatsapp_alert(
            recipient=admin_number,
            remaining_pct=round(
                (1 - (
                    (tenant.get("used_cloud_api", 0) + tenant.get("used_evolution_api", 0)) /
                    max(1, tenant.get("cloud_api_quota", 200) + tenant.get("evolution_api_quota", 300))
                )) * 100, 1
            ),
            reset_date=QuotaNotifier._get_reset_date(tenant),
            tenant=tenant,
        )
        logger.info("Tenant %s: alerta manual enviada a %s", tenant_id, admin_number)
        return {"status": "sent", "recipient": admin_number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enviando alerta: {e}")


# ---------------------------------------------------------------------------
# ENDPOINTS ADMIN (solo super_admin)
# ---------------------------------------------------------------------------

@router.get("/admin/tenants/{tenant_id}/config")
async def admin_get_tenant_config(
    tenant_id: UUID,
    _admin=Depends(solo_super_admin),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Vista completa de la configuración de cuotas de un tenant (solo admin)."""
    tenant = await _get_tenant_row(tenant_id, db)
    # Para admin mostramos tokens enmascarados (no el valor real)
    tenant["byoa_cloud_token"]        = mask_sensitive(tenant.get("byoa_cloud_token"))
    tenant["byoa_evolution_api_key"]  = mask_sensitive(tenant.get("byoa_evolution_api_key"))
    return tenant


@router.post("/admin/tenants/{tenant_id}/reset")
async def admin_reset_quota(
    tenant_id: UUID,
    body: ManualResetRequest,
    _admin=Depends(solo_super_admin),
):
    """Resetea manualmente las cuotas de un tenant con registro de auditoría."""
    result = await manual_reset_tenant(str(tenant_id), body.reason)
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error"))
    return result


@router.post("/admin/plans/{plan_id}/quotas")
async def admin_update_plan_quotas(
    plan_id: str,
    body: PlanQuotaUpdateRequest,
    _admin=Depends(solo_super_admin),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Actualiza las cuotas de un plan global."""
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Sin campos a actualizar")

    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    updates["pid"] = plan_id

    await db.execute(
        text(f"UPDATE plans SET {set_clause} WHERE id = :pid"),
        updates
    )

    logger.info("Plan %s actualizado por admin: %s", plan_id, updates)
    return {"status": "updated", "plan_id": plan_id, "changes": body.model_dump(exclude_none=True)}
