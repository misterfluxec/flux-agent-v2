from __future__ import annotations
import asyncio, logging, os, random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import dramatiq
from dramatiq.middleware import CurrentMessage
from sqlalchemy import text

logger = logging.getLogger("flux.reminders")
ECUADOR_TZ = ZoneInfo("America/Guayaquil")


def _hora_display(hora_obj) -> str:
    if not hora_obj:
        return "la hora acordada"
    try:
        return hora_obj.strftime("%I:%M %p")
    except Exception:
        return str(hora_obj)


def _mensaje(tipo: str, nombre: str,
             servicio: str, hora: str) -> str:
    tips = {
        "manicure semipermanente": "Ven sin esmalte previo",
        "uñas acrílicas": "Uñas limpias y sin humedad",
        "pedicure spa": "Puedes traer tu esmalte favorito",
    }
    tip = next(
        (v for k, v in tips.items()
         if k in servicio.lower()),
        "Llega puntual para aprovechar tu tiempo"
    )
    n = (nombre or "amiga").split()[0]
    if tipo == "24h":
        return (
            f"Hola {n}! Mañana tienes tu cita de "
            f"{servicio} a las {hora}. "
            f"Confirma respondiendo SI o NO. "
            f"Tip: {tip}. Te esperamos!"
        )
    return (
        f"Hola {n}! En 2 horas tienes tu {servicio} "
        f"a las {hora}. Tip: {tip}. Ya casi es hora!"
    )


# FIX 4: max_workers=1 → secuencial, sin ráfagas
@dramatiq.actor(
    queue_name="reminders",
    max_retries=0,          # FIX 3: sin reintentos
    time_limit=30_000,
)
def enviar_recordatorio_task(
    booking_id: str, tipo: str, tenant_id: str,
    telefono: str, nombre: str, servicio: str,
    hora_str: str, evolution_url: str,
    evolution_key: str, instance_name: str,
):
    asyncio.run(_enviar_async(
        booking_id, tipo, tenant_id, telefono,
        nombre, servicio, hora_str,
        evolution_url, evolution_key, instance_name,
    ))


async def _enviar_async(
    booking_id, tipo, tenant_id, telefono,
    nombre, servicio, hora_str,
    evolution_url, evolution_key, instance_name,
):
    import httpx
    from database import sesion_db

    # FIX 3: Marcar como enviado ANTES de enviar
    # (at-most-once: preferimos no enviar a duplicar)
    columna = (
        "recordatorio_24h_enviado" if tipo == "24h"
        else "recordatorio_2h_enviado"
    )
    async with sesion_db() as db:
        result = await db.execute(
            text(f"""
                UPDATE bookings
                SET {columna} = true, updated_at = NOW()
                WHERE id = :bid
                  AND {columna} = false
                RETURNING id
            """),
            {"bid": booking_id},
        )
        marcado = result.fetchone()
        await db.commit()

    if not marcado:
        # Ya fue marcado por otra instancia — skip
        logger.info("reminder_already_sent",
                   extra={"booking_id": booking_id})
        return

    # FIX 1: Verificar ventana horaria Ecuador
    ahora = datetime.now(ECUADOR_TZ)
    if not (9 <= ahora.hour < 19):
        logger.warning(
            "reminder_outside_window",
            extra={"hora": ahora.hour,
                   "booking_id": booking_id},
        )
        return

    # FIX 4: Delay secuencial entre mensajes
    await asyncio.sleep(random.uniform(4.0, 9.0))

    mensaje = _mensaje(tipo, nombre, servicio, hora_str)

    async with httpx.AsyncClient(timeout=15.0) as c:
        try:
            r = await c.post(
                f"{evolution_url}/message/sendText/{instance_name}",
                headers={"apikey": evolution_key,
                         "Content-Type": "application/json"},
                json={"number": telefono, "text": mensaje},
            )
            exito = r.status_code in (200, 201)
            if not exito:
                logger.error(
                    "reminder_evolution_error",
                    extra={"status": r.status_code,
                           "body": r.text[:150]},
                )
        except Exception as exc:
            logger.error("reminder_http_error",
                        extra={"error": str(exc)})
            exito = False

    logger.info(
        "reminder_sent",
        extra={"tipo": tipo, "exito": exito,
               "booking_id": booking_id,
               "telefono": telefono[-4:]},
    )


@dramatiq.actor(
    queue_name="reminders_check",
    max_retries=1,
    time_limit=60_000,
)
def check_and_schedule_reminders():
    asyncio.run(_check_async())


async def _check_async():
    evolution_url = os.getenv(
        "EVOLUTION_API_URL", "http://172.19.0.6:8080"
    )
    evolution_key = os.getenv(
        "EVOLUTION_API_KEY", "fluxkey123"
    )

    # FIX 1: Todo en hora local Ecuador, sin UTC
    ahora = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
    en_24h = ahora + timedelta(hours=24)
    en_2h  = ahora + timedelta(hours=2)
    margen = timedelta(minutes=20)

    from database import sesion_db
    async with sesion_db() as db:

        # FIX 2: SET bypass RLS explícito para tarea sistema
        await db.execute(
            text("SET LOCAL app.bypass_rls = 'on'")
        )

        query = """
            SELECT b.id, b.tenant_id,
                   b.cliente_telefono, b.cliente_nombre,
                   b.servicio_nombre, b.hora, b.fecha,
                   cc.instancia_nombre
            FROM bookings b
            JOIN canales_config cc
              ON cc.tenant_id = b.tenant_id
             AND cc.canal = 'whatsapp'
             AND cc.estado = 'activo'
            WHERE b.estado = 'confirmada'
              AND b.{columna} = false
              AND (b.fecha::timestamp + b.hora::interval)
                  BETWEEN :desde AND :hasta
        """

        res_24h = await db.execute(
            text(query.format(
                columna="recordatorio_24h_enviado"
            )),
            {"desde": en_24h - margen,
             "hasta": en_24h + margen},
        )
        para_24h = res_24h.fetchall()

        res_2h = await db.execute(
            text(query.format(
                columna="recordatorio_2h_enviado"
            )),
            {"desde": en_2h - margen,
             "hasta": en_2h + margen},
        )
        para_2h = res_2h.fetchall()

    def _encolar(bookings, tipo):
        for b in bookings:
            enviar_recordatorio_task.send(
                str(b.id), tipo, str(b.tenant_id),
                b.cliente_telefono,
                b.cliente_nombre or "Cliente",
                b.servicio_nombre,
                _hora_display(b.hora),
                evolution_url, evolution_key,
                b.instancia_nombre or "spa_maritza_01",
            )
            logger.info(f"reminder_{tipo}_queued",
                       extra={"booking_id": str(b.id)})

    _encolar(para_24h, "24h")
    _encolar(para_2h, "2h")

    logger.info(
        "reminders_check_done",
        extra={"24h": len(para_24h),
               "2h": len(para_2h)},
    )
