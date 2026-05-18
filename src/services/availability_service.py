from __future__ import annotations
import logging
from datetime import date, time, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("flux.availability")
ECUADOR_TZ = ZoneInfo("America/Guayaquil")


class AvailabilityService:
    def __init__(self, db: AsyncSession, tenant_id: str):
        self.db = db
        self.tenant_id = tenant_id

    # FIX 2: RLS en método async, no en __init__
    async def _set_rls(self) -> None:
        await self.db.execute(
            text("SELECT set_config("
                 "'app.current_tenant_id',:t,true)"),
            {"t": self.tenant_id},
        )

    async def get_duracion_servicio(
        self, servicio_nombre: str
    ) -> int:
        """FIX 3: Duración real desde catálogo."""
        await self._set_rls()
        r = await self.db.execute(
            text("""
                SELECT duration_minutes FROM catalog_items
                WHERE tenant_id = :tid
                  AND LOWER(name) LIKE
                      LOWER(:srv)
                  AND is_active = TRUE
                LIMIT 1
            """),
            {"tid": self.tenant_id,
             "srv": f"%{servicio_nombre}%"},
        )
        row = r.fetchone()
        return int(row.duration_minutes) if (
            row and row.duration_minutes
        ) else 60  # fallback

    async def get_available_slots(
        self,
        days_ahead: int = 7,
        servicio_duracion: int = 60,
        max_slots: int = 6,
    ) -> list[dict[str, Any]]:
        await self._set_rls()

        # FIX 1: ahora naive para comparar con DB naive
        ahora = datetime.now(ECUADOR_TZ).replace(tzinfo=None)
        hoy = ahora.date()
        slots_disponibles: list[dict] = []

        for delta in range(days_ahead + 1):
            if len(slots_disponibles) >= max_slots:
                break
            fecha = hoy + timedelta(days=delta)
            dia_semana = fecha.weekday()

            horario = await self._get_horario(dia_semana)
            if not horario:
                continue
            if await self._is_blocked(fecha):
                continue

            ocupados = await self._get_ocupados(fecha)
            slots_dia = self._generar_slots_dia(
                fecha,
                horario["apertura"],
                horario["cierre"],
                horario["duracion"],
                servicio_duracion,
                ahora,  # FIX 1: naive
            )

            for slot in slots_dia:
                if len(slots_disponibles) >= max_slots:
                    break
                if not self._choca(
                    slot, servicio_duracion, ocupados
                ):
                    slots_disponibles.append({
                        "fecha": fecha.isoformat(),
                        "hora": slot.strftime("%H:%M"),
                        "dia": self._nombre_dia(dia_semana),
                        "fecha_display": self._fecha_display(
                            fecha, hoy
                        ),
                        "hora_display": slot.strftime(
                            "%-I:%M %p"
                        ),
                    })

        return slots_disponibles

    async def is_slot_available(
        self,
        fecha: date,
        hora: time,
        duracion: int = 60,
    ) -> bool:
        await self._set_rls()
        horario = await self._get_horario(fecha.weekday())
        if not horario:
            return False
        if await self._is_blocked(fecha):
            return False
        ocupados = await self._get_ocupados(fecha)
        slot = datetime.combine(fecha, hora)
        return not self._choca(slot, duracion, ocupados)

    async def _get_horario(
        self, dia_semana: int
    ) -> dict | None:
        r = await self.db.execute(
            text("""
                SELECT hora_apertura, hora_cierre,
                       duracion_slot
                FROM business_hours
                WHERE tenant_id = :tid
                  AND dia_semana = :dia
                  AND es_activo = TRUE
            """),
            {"tid": self.tenant_id, "dia": dia_semana},
        )
        row = r.fetchone()
        if not row:
            return None
        return {
            "apertura": row.hora_apertura,
            "cierre":   row.hora_cierre,
            "duracion": row.duracion_slot,
        }

    async def _is_blocked(self, fecha: date) -> bool:
        r = await self.db.execute(
            text("""
                SELECT 1 FROM blocked_dates
                WHERE tenant_id=:tid AND fecha=:f
            """),
            {"tid": self.tenant_id, "f": fecha},
        )
        return r.fetchone() is not None

    async def _get_ocupados(
        self, fecha: date
    ) -> list[dict]:
        r = await self.db.execute(
            text("""
                SELECT b.hora,
                    COALESCE(ci.duration_minutes, 60)
                        AS duracion
                FROM bookings b
                LEFT JOIN catalog_items ci
                  ON ci.tenant_id = b.tenant_id
                 AND LOWER(ci.name) LIKE
                     LOWER('%'||b.servicio_nombre||'%')
                WHERE b.tenant_id = :tid
                  AND b.fecha = :f
                  AND b.estado IN ('confirmada','pendiente')
            """),
            {"tid": self.tenant_id, "f": fecha},
        )
        return [
            {"hora": row.hora,
             "duracion": int(row.duracion or 60)}
            for row in r.fetchall()
        ]

    def _generar_slots_dia(
        self,
        fecha: date,
        apertura: Any,
        cierre: Any,
        duracion_slot: int,
        duracion_servicio: int,
        ahora: datetime,  # FIX 1: recibe naive
    ) -> list[datetime]:
        if isinstance(apertura, time):
            inicio = datetime.combine(fecha, apertura)
        else:
            inicio = datetime.combine(fecha, apertura)
        if isinstance(cierre, time):
            fin = datetime.combine(fecha, cierre)
        else:
            fin = datetime.combine(fecha, cierre)

        paso = timedelta(minutes=duracion_slot)
        limite = fin - timedelta(minutes=duracion_servicio)
        margen = ahora + timedelta(hours=1)  # naive ✓

        slots = []
        actual = inicio
        while actual <= limite:
            if actual > margen:  # FIX 1: ambos naive ✓
                slots.append(actual)
            actual += paso
        return slots

    def _choca(
        self,
        slot: datetime,
        duracion: int,
        ocupados: list[dict],
    ) -> bool:
        slot_fin = slot + timedelta(minutes=duracion)
        for o in ocupados:
            h = o["hora"]
            inicio_o = datetime.combine(
                slot.date(),
                h if isinstance(h, time) else h,
            )
            fin_o = inicio_o + timedelta(
                minutes=int(o["duracion"])
            )
            if slot < fin_o and slot_fin > inicio_o:
                return True
        return False

    def _nombre_dia(self, dia: int) -> str:
        return ["Lunes","Martes","Miércoles","Jueves",
                "Viernes","Sábado","Domingo"][dia]

    def _fecha_display(
        self, fecha: date, hoy: date
    ) -> str:
        diff = (fecha - hoy).days
        if diff == 0:
            return "hoy"
        if diff == 1:
            return "mañana"
        return (f"el {self._nombre_dia(fecha.weekday())}"
                f" {fecha.day}/{fecha.month}")
