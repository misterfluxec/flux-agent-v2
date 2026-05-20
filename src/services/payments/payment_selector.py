"""
PaymentSelector — Selector interactivo multi-proveedor para WhatsApp.

Diseño: Este módulo SOLO se encarga de la presentación (mensajes/botones
WhatsApp). La generación real de links de pago se delega al PaymentFactory
y a los providers existentes (MercadoPagoProvider, PayPhoneProvider).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any

import httpx

from config import obtener_config
from services.payments.payment_factory import PaymentFactory

logger = logging.getLogger("flux.payment_selector")


# ─── Opciones de pago disponibles ────────────────────────────────────────────

@dataclass
class PaymentOption:
    provider_id: str
    display_name: str
    emoji: str
    description: str
    available_in: list[str] = field(default_factory=list)


PAYMENT_OPTIONS: list[PaymentOption] = [
    PaymentOption(
        provider_id="mercadopago",
        display_name="MercadoPago",
        emoji="💳",
        description="Tarjeta, QR, efectivo — LATAM",
        available_in=["EC", "CO", "MX", "AR", "PE", "CL", "UY"],
    ),
    PaymentOption(
        provider_id="payphone",
        display_name="PayPhone",
        emoji="📱",
        description="Tarjeta de crédito/débito — Ecuador",
        available_in=["EC"],
    ),
    PaymentOption(
        provider_id="transfer",
        display_name="Transferencia bancaria",
        emoji="🔄",
        description="Transferencia directa",
        available_in=["EC", "CO", "MX", "AR", "PE", "CL", "UY"],
    ),
]


# ─── Selector principal ─────────────────────────────────────────────────────

class PaymentSelector:
    """
    Genera mensajes interactivos de selección de pago para WhatsApp
    via Evolution API y delega la creación de links al PaymentFactory.
    """

    def __init__(
        self,
        evolution_url: str,
        evolution_key: str,
        instance_name: str,
        country_code: str = "EC",
    ):
        self.evolution_url = evolution_url.rstrip("/")
        self.evolution_key = evolution_key
        self.instance_name = instance_name
        self.country_code = country_code.upper()

    def _get_options_for_country(self) -> list[PaymentOption]:
        return [
            o for o in PAYMENT_OPTIONS
            if self.country_code in o.available_in
        ]

    # ── Enviar mensaje interactivo con opciones ──────────────────────────

    async def send_payment_selector(
        self,
        to: str,
        servicio: str,
        monto: float,
        booking_id: str,
        currency: str = "USD",
    ) -> dict:
        """
        Envía mensaje interactivo con opciones de pago al WhatsApp del cliente.
        Usa botones de Evolution API (max 3). Fallback a texto plano.
        """
        options = self._get_options_for_country()[:3]

        opciones_texto = "\n".join(
            f"{o.emoji} *{o.provider_id.upper()}* — "
            f"{o.display_name}: {o.description}"
            for o in options
        )

        mensaje = (
            f"💰 *Pago para tu cita*\n\n"
            f"📋 Servicio: {servicio}\n"
            f"💵 Total: {currency} {monto:.2f}\n\n"
            f"¿Cómo prefieres pagar?\n\n"
            f"{opciones_texto}\n\n"
            f"Responde con el nombre del método "
            f"(ej: MERCADOPAGO, PAYPHONE, TRANSFER)"
        )

        headers = {
            "apikey": self.evolution_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=15.0) as c:
            # Intentar botones interactivos (Evolution API v2)
            try:
                buttons_payload = {
                    "number": to,
                    "title": f"Pago — {servicio}",
                    "description": mensaje,
                    "footer": "Spa de Uñas Maritza",
                    "buttons": [
                        {
                            "buttonId": f"pay_{o.provider_id}_{booking_id}",
                            "buttonText": {
                                "displayText": f"{o.emoji} {o.display_name}"
                            },
                            "type": 1,
                        }
                        for o in options
                    ],
                }
                r = await c.post(
                    f"{self.evolution_url}/message/"
                    f"sendButtons/{self.instance_name}",
                    headers=headers,
                    json=buttons_payload,
                )
                if r.status_code in (200, 201):
                    logger.info(
                        "payment_selector_buttons_sent",
                        extra={"to": to[-4:], "booking_id": booking_id},
                    )
                    return {"status": "sent", "type": "buttons"}
            except Exception:
                pass

            # Fallback: texto plano
            r = await c.post(
                f"{self.evolution_url}/message/"
                f"sendText/{self.instance_name}",
                headers=headers,
                json={"number": to, "text": mensaje},
            )
            logger.info("payment_selector_text_sent", extra={"to": to[-4:]})
            return {"status": "sent", "type": "text"}

    # ── Generar link de pago usando Factory existente ────────────────────

    async def generate_payment_link(
        self,
        provider_id: str,
        order_id: str,
        amount: float,
        description: str,
        currency: str = "USD",
        tenant_config: Dict[str, Any] | None = None,
    ) -> str:
        """
        Genera el link de pago delegando al PaymentFactory existente.
        Para 'transfer' retorna instrucciones textuales.
        """
        cfg = tenant_config or {}
        settings = obtener_config()

        if provider_id == "transfer":
            return self._transfer_info(cfg)

        # Inyectar config global si el tenant no tiene tokens propios
        if provider_id == "mercadopago" and not cfg.get("mp_access_token"):
            cfg["mp_access_token"] = settings.mp_access_token
        if provider_id == "payphone" and not cfg.get("payphone_token"):
            cfg["payphone_token"] = settings.payphone_token

        try:
            provider = PaymentFactory.get_provider(provider_id)
            result = await provider.create_payment_link(
                order_id=order_id,
                amount=amount,
                currency=currency,
                description=description,
                tenant_config=cfg,
            )
            return result.get("init_point", "")
        except Exception as exc:
            logger.error(
                "payment_link_error",
                extra={"provider": provider_id, "error": str(exc)},
            )
            return ""

    @staticmethod
    def _transfer_info(cfg: dict) -> str:
        return (
            f"Datos para transferencia:\n"
            f"Banco: {cfg.get('bank', 'Banco Pichincha')}\n"
            f"Cuenta: {cfg.get('account', 'Consultar en el spa')}\n"
            f"Tipo: {cfg.get('account_type', 'Corriente')}\n"
            f"Nombre: {cfg.get('account_name', 'Maritza Mendoza')}\n"
            f"Envía comprobante por WhatsApp para confirmar."
        )
