from __future__ import annotations
import json, logging, re
from datetime import datetime, date
from typing import Optional
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger("flux.booking_extractor")

EXTRACT_PROMPT = """Analiza esta conversación de WhatsApp 
entre una clienta y Valentina (agente del Spa de Uñas).

CONVERSACIÓN:
{historia}

Determina si se confirmó una cita. Responde SOLO con JSON:
{{
  "booking_confirmed": true/false,
  "servicio": "nombre exacto del servicio o null",
  "fecha": "YYYY-MM-DD o null (si dice 'hoy' usa {hoy}, 
            'mañana' usa {manana})",
  "hora": "HH:MM en formato 24h o null",
  "cliente_nombre": "nombre si lo mencionó o null",
  "notas": "detalles adicionales relevantes o null"
}}

Si no hay cita confirmada con fecha Y hora específica, 
booking_confirmed debe ser false."""


class BookingExtractor:
    def __init__(self, ollama_url: str = "http://fluxagent-ollama:11434"):
        self.ollama_url = ollama_url

    async def extract(
        self,
        historia: list[dict],
        telefono: str,
        tenant_id: str,
        db: AsyncSession,
    ) -> Optional[dict]:
        # Construir texto de conversación
        conv_text = "\n".join([
            f"{'Cliente' if m.get('rol') == 'usuario' else 'Valentina'}: {m.get('contenido','')}"
            for m in historia[-10:]  # últimas 10 interacciones
        ])

        hoy = date.today().isoformat()
        from datetime import timedelta
        manana = (date.today() + timedelta(days=1)).isoformat()

        prompt = EXTRACT_PROMPT.format(
            historia=conv_text,
            hoy=hoy,
            manana=manana,
        )

        try:
            async with httpx.AsyncClient(timeout=30.0) as c:
                r = await c.post(
                    f"{self.ollama_url}/api/chat",
                    json={
                        "model": "qwen2.5:3b",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "stream": False,
                    },
                )
                r.raise_for_status()
                raw = r.json()["message"]["content"]
        except Exception as exc:
            logger.warning("extractor_llm_error",
                          extra={"error": str(exc)})
            return None

        # Extraer JSON de la respuesta
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not match:
                return None
            data = json.loads(match.group())
        except Exception:
            return None

        if not data.get("booking_confirmed"):
            return None
        if not data.get("fecha") or not data.get("hora"):
            return None

        # Buscar precio en catálogo
        precio = 0.0
        servicio_nombre = data.get("servicio", "Servicio spa")
        try:
            res = await db.execute(
                text("""
                    SELECT price FROM catalog_items
                    WHERE tenant_id = :tid
                      AND LOWER(name) LIKE LOWER(:srv)
                      AND is_active = TRUE
                    LIMIT 1
                """),
                {"tid": tenant_id,
                 "srv": f"%{servicio_nombre}%"},
            )
            row = res.fetchone()
            if row:
                precio = float(row.price)
        except Exception:
            pass

        # Verificar que no existe ya una cita igual
        try:
            exists = await db.execute(
                text("""
                    SELECT id FROM bookings
                    WHERE tenant_id = :tid
                      AND cliente_telefono = :tel
                      AND fecha = :fecha
                      AND hora = :hora
                      AND estado != 'cancelada'
                """),
                {
                    "tid": tenant_id,
                    "tel": telefono,
                    "fecha": data["fecha"],
                    "hora": data["hora"],
                },
            )
            if exists.fetchone():
                logger.info("booking_already_exists",
                           extra={"telefono": telefono[-4:]})
                return None
        except Exception:
            pass

        # Verificar que el slot está disponible (FIX 3: duración real del servicio)
        try:
            from services.availability_service import AvailabilityService
            from datetime import date as _date, time as _time

            avail_svc = AvailabilityService(db=db, tenant_id=tenant_id)
            duracion_real = await avail_svc.get_duracion_servicio(servicio_nombre)

            fecha_obj = _date.fromisoformat(data["fecha"])
            hora_parts = data["hora"].split(":")
            hora_obj = _time(int(hora_parts[0]), int(hora_parts[1]))

            disponible = await avail_svc.is_slot_available(
                fecha=fecha_obj,
                hora=hora_obj,
                duracion=duracion_real,
            )
            if not disponible:
                logger.warning(
                    "booking_slot_not_available",
                    extra={"fecha": data["fecha"], "hora": data["hora"]},
                )
                return None  # No guardar si está ocupado
        except Exception as exc:
            logger.warning("booking_avail_check_failed", extra={"error": str(exc)})

        # Guardar la cita
        try:
            result = await db.execute(
                text("""
                    INSERT INTO bookings (
                        tenant_id, cliente_nombre,
                        cliente_telefono, servicio_nombre,
                        servicio_precio, fecha, hora,
                        estado, canal, notas
                    ) VALUES (
                        :tid, :nombre, :tel, :srv,
                        :precio, :fecha, :hora,
                        'confirmada', 'whatsapp', :notas
                    ) RETURNING id
                """),
                {
                    "tid": tenant_id,
                    "nombre": data.get("cliente_nombre", "Cliente WhatsApp"),
                    "tel": telefono,
                    "srv": servicio_nombre,
                    "precio": precio,
                    "fecha": data["fecha"],
                    "hora": data["hora"],
                    "notas": data.get("notas", ""),
                },
            )
            await db.commit()
            booking_id = result.fetchone()[0]
            logger.info(
                "booking_auto_saved",
                extra={
                    "id": str(booking_id),
                    "servicio": servicio_nombre,
                    "fecha": data["fecha"],
                    "hora": data["hora"],
                    "telefono": telefono[-4:],
                },
            )
            return {
                "id": str(booking_id),
                "servicio": servicio_nombre,
                "fecha": data["fecha"],
                "hora": data["hora"],
                "precio": precio,
            }
        except Exception as exc:
            logger.error("booking_save_error",
                        extra={"error": str(exc)})
            return None
