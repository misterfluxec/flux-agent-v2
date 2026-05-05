"""
FLUXAGENT V2 — QUOTA NOTIFIER
================================
Detecta cuando un tenant usa >90% de su cuota y envía:
  1. Una bandera en base de datos (para el banner del dashboard)
  2. Un mensaje de WhatsApp al número de admin del tenant (si está configurado)

Previene spam: solo notifica 1 vez por período de renovación.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class QuotaNotifier:
    """Verifica y envía notificaciones cuando la cuota está por agotarse."""

    LOW_QUOTA_THRESHOLD = 0.10  # 10% restante = alerta

    @classmethod
    async def check_and_notify(
        cls,
        tenant: dict,
        db: AsyncSession,
    ) -> bool:
        """
        Verifica si el tenant está por debajo del umbral y notifica si corresponde.

        Args:
            tenant: Fila de la BD con columnas de migración 008.
            db    : Sesión activa de SQLAlchemy.

        Returns:
            True si se envió una notificación, False si no fue necesario.
        """
        total_quota = tenant.get("cloud_api_quota", 0) + tenant.get("evolution_api_quota", 0)
        if total_quota <= 0 or total_quota == -2:  # -1 + -1 = cuota ilimitada
            return False

        used_total = tenant.get("used_cloud_api", 0) + tenant.get("used_evolution_api", 0)

        usage_ratio = used_total / total_quota
        remaining_ratio = 1 - usage_ratio

        if remaining_ratio > cls.LOW_QUOTA_THRESHOLD:
            return False  # Aún hay cuota suficiente

        # Verificar si ya se notificó en este período (evitar spam)
        if cls._already_notified_this_period(tenant):
            return False

        tenant_id = tenant.get("id")
        reset_date = cls._get_reset_date(tenant)

        logger.info(
            "Tenant %s: cuota baja (%.1f%% restante) → enviando notificación",
            tenant_id, remaining_ratio * 100
        )

        # 1. Marcar como notificado en la BD
        await cls._mark_notified(tenant_id, db)

        # 2. Notificación por WhatsApp al admin (si tiene número configurado)
        admin_number = tenant.get("admin_whatsapp_number")
        if admin_number:
            await cls._send_whatsapp_alert(
                recipient=admin_number,
                remaining_pct=round(remaining_ratio * 100, 1),
                reset_date=reset_date,
                tenant=tenant,
            )

        return True

    # ------------------------------------------------------------------
    # Helpers privados
    # ------------------------------------------------------------------

    @staticmethod
    def _already_notified_this_period(tenant: dict) -> bool:
        """Verifica si ya se notificó en el período de renovación actual."""
        notified_at = tenant.get("quota_low_notified_at")
        reset_at    = tenant.get("last_quota_reset_at")

        if not notified_at:
            return False

        # Si la notificación fue posterior al último reset, ya se notificó este período
        if reset_at and isinstance(notified_at, datetime) and isinstance(reset_at, datetime):
            return notified_at > reset_at

        return False

    @staticmethod
    def _get_reset_date(tenant: dict) -> str:
        """Calcula la fecha de próximo reset."""
        reset_at = tenant.get("last_quota_reset_at")
        if reset_at and isinstance(reset_at, datetime):
            next_reset = reset_at + timedelta(days=30)
            return next_reset.strftime("%d/%m/%Y")
        return "próximo mes"

    @staticmethod
    async def _mark_notified(tenant_id, db: AsyncSession) -> None:
        """Registra timestamp de notificación para evitar spam."""
        await db.execute(
            text("""
                UPDATE tenants
                SET quota_low_notified_at = NOW()
                WHERE id = :tenant_id
            """),
            {"tenant_id": str(tenant_id)},
        )

    @staticmethod
    async def _send_whatsapp_alert(
        recipient: str,
        remaining_pct: float,
        reset_date: str,
        tenant: dict,
    ) -> None:
        """
        Envía alerta de cuota baja por WhatsApp usando Evolution API global.
        Usa texto plano (no template) para máxima compatibilidad.
        """
        try:
            from services.whatsapp_sender import send_text_message
            from config import obtener_config

            cfg = obtener_config()
            message = (
                f"⚠️ *FluxAgent — Aviso de Cuota*\n\n"
                f"Tu cuota mensual está al *{remaining_pct}% restante*.\n"
                f"🔄 Se renovará el: *{reset_date}*\n\n"
                f"💡 Visita tu panel para más detalles:\n"
                f"app.labodegaec.com/dashboard/conectores"
            )

            instance_name = tenant.get("evolution_instance", "default")
            await send_text_message(instance_name, recipient, message)
            logger.info("Notificación de cuota baja enviada a %s", recipient)

        except Exception as e:
            # No interrumpir el flujo de mensajería por una notificación fallida
            logger.warning("No se pudo enviar alerta de cuota a %s: %s", recipient, e)


def build_quota_banner_data(tenant: dict) -> Optional[dict]:
    """
    Construye los datos para el banner de cuota baja en el frontend.
    Retorna None si la cuota está OK.

    El frontend llama a GET /api/v1/quota/my-config y usa este campo
    para mostrar el banner automáticamente.
    """
    total_quota = tenant.get("cloud_api_quota", 0) + tenant.get("evolution_api_quota", 0)
    if total_quota <= 0 or total_quota == -2:
        return None

    used = tenant.get("used_cloud_api", 0) + tenant.get("used_evolution_api", 0)
    remaining_ratio = 1 - (used / total_quota)

    if remaining_ratio > QuotaNotifier.LOW_QUOTA_THRESHOLD:
        return None

    reset_date = QuotaNotifier._get_reset_date(tenant)

    return {
        "show_banner": True,
        "remaining_pct": round(remaining_ratio * 100, 1),
        "reset_date": reset_date,
        "message": (
            f"⚠️ Te queda solo el {round(remaining_ratio * 100, 1)}% de tu cuota mensual. "
            f"Se renueva el {reset_date}."
        ),
    }
