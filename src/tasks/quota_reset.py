"""
FLUXAGENT V2 — QUOTA RESET TASK (APScheduler)
================================================
Tarea programada que se ejecuta diariamente a las 02:00 UTC.
Resetea los contadores de cuota de tenants cuyo período venció.

Integración en main.py:
    from tasks.quota_reset import start_quota_scheduler, stop_quota_scheduler
    app.add_event_handler("startup", start_quota_scheduler)
    app.add_event_handler("shutdown", stop_quota_scheduler)
"""

import logging
from datetime import timedelta, timezone, datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

from database import sesion_db

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _run_quota_reset() -> dict:
    """
    Core de la tarea: busca tenants con período vencido y resetea sus contadores.
    Registra log de auditoría por cada tenant reseteado.
    """
    reset_count = 0
    tenant_ids = []

    try:
        async with sesion_db() as db:
            # Buscar tenants cuyo período de 30 días venció
            result = await db.execute(text("""
                SELECT t.id, t.last_quota_reset_at, p.reset_period_days
                FROM tenants t
                LEFT JOIN plans p ON t.plan = p.id
                WHERE (t.last_quota_reset_at + INTERVAL '1 day' * COALESCE(p.reset_period_days, 30))
                      <= NOW()
                  AND (t.used_cloud_api > 0 OR t.used_evolution_api > 0)
            """))
            tenants_to_reset = result.fetchall()

            for row in tenants_to_reset:
                tenant_id = str(row.id)
                await db.execute(text("""
                    UPDATE tenants
                    SET used_cloud_api         = 0,
                        used_evolution_api     = 0,
                        last_quota_reset_at    = NOW(),
                        quota_low_notified_at  = NULL
                    WHERE id = :tid
                """), {"tid": tenant_id})

                # Log de auditoría en whatsapp_usage para trazabilidad
                await db.execute(text("""
                    INSERT INTO whatsapp_usage (
                        tenant_id, recipient_phone, conversation_type,
                        channel_used, quota_source, send_status,
                        meta_cost_usd, first_message_at, last_message_at
                    ) VALUES (
                        :tid, 'system', 'service',
                        'evolution', 'global_pool', 'sent',
                        0, NOW(), NOW()
                    )
                """), {"tid": tenant_id})

                tenant_ids.append(tenant_id)
                reset_count += 1

            await db.commit()

    except Exception as e:
        logger.error("Error durante quota reset automático: %s", e, exc_info=True)
        return {"reset_count": 0, "error": str(e)}

    if reset_count:
        logger.info(
            "✅ Quota reset automático: %d tenants reseteados: %s",
            reset_count, tenant_ids
        )
    else:
        logger.debug("⏭️ Quota reset: ningún tenant necesita reset en este momento")

    return {"reset_count": reset_count, "tenant_ids": tenant_ids}


async def manual_reset_tenant(tenant_id: str, reason: str = "manual_override") -> dict:
    """
    Resetea la cuota de un tenant específico de forma manual.
    Llamado desde el endpoint de admin.
    """
    from uuid import UUID
    try:
        async with sesion_db() as db:
            result = await db.execute(text("""
                UPDATE tenants
                SET used_cloud_api         = 0,
                    used_evolution_api     = 0,
                    last_quota_reset_at    = NOW(),
                    quota_low_notified_at  = NULL
                WHERE id = :tid
                RETURNING id, last_quota_reset_at
            """), {"tid": tenant_id})
            row = result.fetchone()
            await db.commit()

            if not row:
                return {"success": False, "error": "Tenant no encontrado"}

            logger.info(
                "🔧 Reset manual de cuotas: tenant=%s, motivo=%s", tenant_id, reason
            )
            return {
                "success": True,
                "tenant_id": tenant_id,
                "reset_at": str(row.last_quota_reset_at),
                "reason": reason,
            }
    except Exception as e:
        logger.error("Error en reset manual de tenant %s: %s", tenant_id, e)
        return {"success": False, "error": str(e)}


async def start_quota_scheduler() -> None:
    """Inicia el scheduler en el startup de FastAPI."""
    global _scheduler
    _scheduler = AsyncIOScheduler(timezone="UTC")
    _scheduler.add_job(
        _run_quota_reset,
        trigger=CronTrigger(hour=2, minute=0),  # 02:00 UTC diario
        id="quota_reset_daily",
        name="Reset automático de cuotas diario",
        replace_existing=True,
        misfire_grace_time=3600,  # Si falla, intentar hasta 1 hora después
    )
    _scheduler.start()
    logger.info("⏰ Quota reset scheduler iniciado (02:00 UTC diario)")


async def stop_quota_scheduler() -> None:
    """Detiene el scheduler en el shutdown de FastAPI."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("⏰ Quota reset scheduler detenido")
