import logging
import hashlib
import json
from datetime import datetime, timezone
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis

from database import obtener_sesion
from auth import PayloadToken, get_usuario_actual
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

redis_client = redis.Redis.from_url(config.redis_url)

# =============================================================================
# PLAN CAPABILITIES: Feature Flags Estáticos por Plan
# =============================================================================

PLAN_CAPABILITIES = {
    "starter": {
        "can_use_realtime_ops": False,
        "can_use_predictive_ai": False,
        "can_export_pdf": False,
        "can_use_advanced_analytics": False,
        "allowed_channels": ["whatsapp"],
    },
    "growth": {
        "can_use_realtime_ops": True,
        "can_use_predictive_ai": False,
        "can_export_pdf": True,
        "can_use_advanced_analytics": True,
        "allowed_channels": ["whatsapp", "telegram", "webchat"],
    },
    "enterprise": {
        "can_use_realtime_ops": True,
        "can_use_predictive_ai": True,
        "can_export_pdf": True,
        "can_use_advanced_analytics": True,
        "allowed_channels": "*",
    }
}

# =============================================================================
# QUOTA TAXONOMY: Operacionales vs Facturables
# Separación crítica para throttling y monetización independientes.
# =============================================================================

# Cuotas OPERACIONALES: protegen infraestructura y estabilidad.
# Se pueden resetear, throttlear o hacer burst-control SIN impactar billing.
OPERATIONAL_QUOTAS = {
    "messages_per_minute": {
        "starter": 5,
        "growth": 30,
        "enterprise": -1,   # Sin límite
        "window_sec": 60,
        "error": "Demasiados mensajes. Espera un momento."
    },
    "concurrent_calls": {
        "starter": 1,
        "growth": 5,
        "enterprise": -1,
        "window_sec": None,  # Estado real, no ventana de tiempo
        "error": "Límite de llamadas simultáneas alcanzado."
    },
    "active_workflows": {
        "starter": 3,
        "growth": 20,
        "enterprise": -1,
        "window_sec": None,
        "error": "Límite de workflows activos alcanzado. Upgrade para más."
    },
}

# Cuotas FACTURABLES: impactan directamente el billing del tenant.
# Nunca resetear en burst-control, solo validar contra límite mensual del contrato.
BILLABLE_QUOTAS = {
    "monthly_messages": {
        "starter": 500,
        "growth": 10000,
        "enterprise": -1,
        "error": "Cuota mensual de mensajes agotada."
    },
    "voice_minutes": {
        "starter": 0,
        "growth": 60,
        "enterprise": -1,
        "error": "Minutos de voz agotados. Actualiza tu plan."
    },
    "pdf_exports": {
        "starter": 0,
        "growth": 50,
        "enterprise": -1,
        "error": "Exportaciones PDF agotadas este mes."
    },
}


class PlanManager:
    """
    Autoridad central de billing, features y límites por plan.
    Maneja quotas operacionales (infraestructura) y facturables (monetización) por separado.
    """

    @staticmethod
    def _current_month_str() -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y-%m")

    @staticmethod
    def _current_day_str() -> str:
        return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")

    @staticmethod
    async def verificar_acceso_tenant(tenant_id: UUID, db: AsyncSession):
        """Versión programática para usar desde webhooks o procesos internos."""
        query = text("SELECT plan, creado_en, features, usage_limits FROM tenants WHERE id = :tenant_id")
        result = await db.execute(query, {"tenant_id": str(tenant_id)})
        tenant = result.fetchone()

        if not tenant:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")

        plan = tenant.plan
        creado_en = tenant.creado_en

        if plan == "starter":
            if creado_en.tzinfo is None:
                creado_en = creado_en.replace(tzinfo=timezone.utc)
            dias_activo = (datetime.now(tz=timezone.utc) - creado_en).days
            if dias_activo > 7:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Tu prueba gratuita de 7 días ha finalizado. Por favor, actualiza tu plan en Facturación."
                )

        return {"plan": plan, "features": tenant.features, "limits": tenant.usage_limits}

    @staticmethod
    async def verificar_acceso(
        usuario: PayloadToken = Depends(get_usuario_actual),
        db: AsyncSession = Depends(obtener_sesion)
    ):
        """Valida que el tenant tenga acceso general (usado en Dependencias)."""
        return await PlanManager.verificar_acceso_tenant(UUID(usuario.tenant_id), db)

    # =========================================================================
    # FEATURE FLAGS
    # =========================================================================

    @staticmethod
    async def check_capability(tenant_id: UUID, db: AsyncSession, capability: str) -> bool:
        """Verifica un feature flag estático basado en el plan del tenant."""
        tenant_info = await PlanManager.verificar_acceso_tenant(tenant_id, db)
        plan = tenant_info["plan"]
        caps = PLAN_CAPABILITIES.get(plan, PLAN_CAPABILITIES["starter"])

        has_cap = caps.get(capability, False)
        if not has_cap:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu plan '{plan}' no incluye la funcionalidad: '{capability}'."
            )
        return True

    @staticmethod
    def verificar_capability(capability: str):
        """Dependencia FastAPI para feature flags estáticos."""
        async def _verificar(
            usuario: PayloadToken = Depends(get_usuario_actual),
            db: AsyncSession = Depends(obtener_sesion)
        ):
            return await PlanManager.check_capability(UUID(usuario.tenant_id), db, capability)
        return _verificar

    @staticmethod
    async def check_feature_tenant(tenant_id: UUID, db: AsyncSession, feature_name: str):
        """Verifica feature habilitado en el campo features del tenant (legacy DB flags)."""
        tenant_info = await PlanManager.verificar_acceso_tenant(tenant_id, db)
        features = tenant_info["features"]
        if not features or not features.get(feature_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tu plan actual no incluye la funcionalidad: '{feature_name}'."
            )
        return True

    @staticmethod
    def verificar_feature(feature_name: str):
        """Dependencia para proteger endpoints específicos (legacy limits)."""
        async def _verificar(
            usuario: PayloadToken = Depends(get_usuario_actual),
            db: AsyncSession = Depends(obtener_sesion)
        ):
            return await PlanManager.check_feature_tenant(UUID(usuario.tenant_id), db, feature_name)
        return _verificar

    # =========================================================================
    # CUOTAS OPERACIONALES (Burst-control / infraestructura)
    # =========================================================================

    @staticmethod
    async def check_operational_quota(tenant_id: str, plan: str, quota_name: str, count: int = 1) -> bool:
        """
        Verifica límite operacional (protección de infraestructura).
        Usa ventana de tiempo en Redis. No bloquea billing si se throttlea.
        """
        quota_def = OPERATIONAL_QUOTAS.get(quota_name)
        if not quota_def:
            return True  # Quota desconocida: no bloquear

        limit = quota_def.get(plan, quota_def.get("starter", 0))
        if limit == -1:
            return True  # Sin límite en este plan

        window_sec = quota_def.get("window_sec")
        redis_key = (
            f"ops:{tenant_id}:{quota_name}"
            if not window_sec
            else f"ops:{tenant_id}:{quota_name}:{int(datetime.now(tz=timezone.utc).timestamp()) // window_sec}"
        )

        try:
            current = int(redis_client.get(redis_key) or 0)
            if current + count > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=quota_def["error"],
                    headers={"X-Quota-Type": "operational", "X-Quota-Limit": str(limit)}
                )
            pipe = redis_client.pipeline()
            pipe.incrby(redis_key, count)
            if window_sec:
                pipe.expire(redis_key, window_sec * 2)  # TTL generoso para limpiar
            pipe.execute()
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis error en check_operational_quota({quota_name}): {e}")

        return True

    # =========================================================================
    # CUOTAS FACTURABLES (Billing / monetización)
    # =========================================================================

    @staticmethod
    async def check_billable_quota(tenant_id: str, plan: str, quota_name: str, count: int = 1) -> bool:
        """
        Verifica límite facturable mensual.
        NUNCA throttlear en burst-control. Solo validar contra límite del contrato.
        """
        quota_def = BILLABLE_QUOTAS.get(quota_name)
        if not quota_def:
            return True

        limit = quota_def.get(plan, quota_def.get("starter", 0))
        if limit == -1:
            return True

        mes = PlanManager._current_month_str()
        redis_key = f"billing:{tenant_id}:{mes}:{quota_name}"

        try:
            current = int(redis_client.get(redis_key) or 0)
            if current + count > limit:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail=quota_def["error"],
                    headers={"X-Quota-Type": "billable", "X-Quota-Name": quota_name, "X-Quota-Limit": str(limit)}
                )
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"Redis error en check_billable_quota({quota_name}): {e}")

        return True

    @staticmethod
    def registrar_uso_facturable(tenant_id: str, quota_name: str, count: int = 1):
        """
        Incrementa el contador mensual facturable en Redis.
        Llamar DESPUÉS de confirmar que la operación fue exitosa.
        """
        mes = PlanManager._current_month_str()
        redis_key = f"billing:{tenant_id}:{mes}:{quota_name}"
        try:
            redis_client.incrby(redis_key, count)
            redis_client.expire(redis_key, 86400 * 35)  # ~1 mes + 5 días buffer
        except Exception as e:
            logger.error(f"Error registrando uso facturable {quota_name}: {e}")

    # =========================================================================
    # MÉTODOS LEGACY (compatibilidad hacia atrás)
    # =========================================================================

    @staticmethod
    async def check_limite_diario_tenant(tenant_id: UUID, db: AsyncSession, resource: str, count: int = 1):
        """Mantiene compatibilidad con llamadas antiguas al check diario."""
        tenant_info = await PlanManager.verificar_acceso_tenant(tenant_id, db)
        plan = tenant_info["plan"]

        # Redirigir al nuevo sistema de quotas facturables si aplica
        billable_map = {"messages": "monthly_messages", "audio_sec": "voice_minutes"}
        if resource in billable_map:
            return await PlanManager.check_billable_quota(str(tenant_id), plan, billable_map[resource], count)

        # Fallback al sistema anterior para resources no migrados
        limits = tenant_info["limits"]
        key = f"daily_{resource}"
        max_limit = limits.get(key, 0)

        if max_limit == -1 or max_limit >= 99999:
            return True

        hoy = PlanManager._current_day_str()
        redis_key = f"usage:{tenant_id}:{hoy}:{resource}"

        try:
            current_usage = int(redis_client.get(redis_key) or 0)
        except Exception as e:
            logger.error(f"Redis error legacy check_limite_diario: {e}")
            current_usage = 0

        if current_usage + count > max_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Has alcanzado el límite diario de {resource} ({max_limit}). Haz upgrade para obtener más capacidad."
            )
        return True

    @staticmethod
    def verificar_limite_diario(resource: str, count: int = 1):
        """Dependencia FastAPI (legacy)."""
        async def _verificar(
            usuario: PayloadToken = Depends(get_usuario_actual),
            db: AsyncSession = Depends(obtener_sesion)
        ):
            return await PlanManager.check_limite_diario_tenant(UUID(usuario.tenant_id), db, resource, count)
        return _verificar

    @staticmethod
    def registrar_uso(tenant_id: str, resource: str, count: int = 1):
        """Legacy: registra uso diario y mensual. Preferir registrar_uso_facturable."""
        hoy = PlanManager._current_day_str()
        mes = PlanManager._current_month_str()

        redis_key_daily = f"usage:{tenant_id}:{hoy}:{resource}"
        redis_key_monthly = f"usage:{tenant_id}:{mes}:{resource}"
        try:
            pipe = redis_client.pipeline()
            pipe.incrby(redis_key_daily, count)
            pipe.expire(redis_key_daily, 86400 * 2)
            pipe.incrby(redis_key_monthly, count)
            pipe.expire(redis_key_monthly, 86400 * 32)
            pipe.execute()
        except Exception as e:
            logger.error(f"Error registrando uso en Redis: {e}")

    @staticmethod
    async def check_limite_mensual_tenant(tenant_id: UUID, db: AsyncSession, resource: str, count: int = 1):
        """Legacy: verifica límite mensual. Prefer check_billable_quota."""
        tenant_info = await PlanManager.verificar_acceso_tenant(tenant_id, db)
        plan = tenant_info["plan"]
        limits = tenant_info["limits"]

        key = f"monthly_{resource}"
        max_limit = limits.get(key, 0)

        if max_limit == -1 or max_limit >= 99999:
            return True

        mes = PlanManager._current_month_str()
        redis_key = f"usage:{tenant_id}:{mes}:{resource}"

        try:
            current_usage = int(redis_client.get(redis_key) or 0)
        except Exception as e:
            logger.error(f"Redis error legacy check_limite_mensual: {e}")
            current_usage = 0

        if current_usage + count > max_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Has alcanzado el límite mensual de {resource} ({max_limit}). Haz upgrade para obtener más capacidad."
            )
        return True
