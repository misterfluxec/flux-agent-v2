import logging
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

# Usar el string de conexión a redis desde la configuración
redis_client = redis.Redis.from_url(config.redis_url)

class PlanManager:
    """
    Middleware/Dependencia para validar límites de facturación, features y trial.
    """
    
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
        """
        Valida que el tenant tenga acceso general (usado en Dependencias).
        """
        return await PlanManager.verificar_acceso_tenant(UUID(usuario.tenant_id), db)

    @staticmethod
    async def check_feature_tenant(tenant_id: UUID, db: AsyncSession, feature_name: str):
        """Versión programática de check de feature"""
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
        """Dependencia para proteger endpoints específicos"""
        async def _verificar(
            usuario: PayloadToken = Depends(get_usuario_actual),
            db: AsyncSession = Depends(obtener_sesion)
        ):
            return await PlanManager.check_feature_tenant(UUID(usuario.tenant_id), db, feature_name)
        return _verificar

    @staticmethod
    async def check_limite_diario_tenant(tenant_id: UUID, db: AsyncSession, resource: str, count: int = 1):
        """Versión programática de check de límites"""
        tenant_info = await PlanManager.verificar_acceso_tenant(tenant_id, db)
        limits = tenant_info["limits"]
        
        resource_map = {
            "messages": "daily_messages",
            "audio_sec": "daily_audio_sec",
            "images": "daily_images"
        }
        key = resource_map.get(resource, f"daily_{resource}")
        max_limit = limits.get(key, 0)
        
        if max_limit == -1 or max_limit >= 99999:
            return True

        hoy = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        redis_key = f"usage:{tenant_id}:{hoy}:{resource}"

        try:
            current_usage = redis_client.get(redis_key)
            current_usage = int(current_usage) if current_usage else 0
        except Exception as e:
            logger.error(f"Error accediendo a Redis para límites: {e}")
            current_usage = 0

        if current_usage + count > max_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Has alcanzado el límite diario de {resource} ({max_limit}). Haz upgrade para obtener más capacidad."
            )
        return True

    @staticmethod
    def verificar_limite_diario(resource: str, count: int = 1):
        """Dependencia FastAPI"""
        async def _verificar(
            usuario: PayloadToken = Depends(get_usuario_actual),
            db: AsyncSession = Depends(obtener_sesion)
        ):
            return await PlanManager.check_limite_diario_tenant(UUID(usuario.tenant_id), db, resource, count)
        return _verificar

    @staticmethod
    def registrar_uso(tenant_id: str, resource: str, count: int = 1):
        hoy = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        redis_key = f"usage:{tenant_id}:{hoy}:{resource}"
        try:
            redis_client.incrby(redis_key, count)
            redis_client.expire(redis_key, 86400 * 2)
        except Exception as e:
            logger.error(f"Error registrando uso en Redis: {e}")
