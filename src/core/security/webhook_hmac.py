"""
Webhook HMAC Signature Validator
=================================
Dependencia FastAPI reutilizable para validar firmas HMAC-SHA256 de webhooks
entrantes (Evolution API / MercadoPago / cualquier proveedor que lo soporte).

Comportamiento:
  - Si el secret está vacío en config → pasa sin validar (modo desarrollo)
  - Si el secret está configurado → valida firma o devuelve 401

Uso en un endpoint:
    from core.security.webhook_hmac import verificar_hmac_evolution

    @router.post("/whatsapp")
    async def evolution_webhook(
        request: Request,
        _: None = Depends(verificar_hmac_evolution),
    ):
        ...
"""

import hashlib
import hmac
import logging

from fastapi import Depends, HTTPException, Request, status

from config import obtener_config

logger = logging.getLogger(__name__)


async def _leer_cuerpo_raw(request: Request) -> bytes:
    """Lee el body raw del request y lo guarda en state para no consumirlo dos veces."""
    if not hasattr(request.state, "raw_body"):
        request.state.raw_body = await request.body()
    return request.state.raw_body


def _calcular_hmac(secret: str, payload: bytes) -> str:
    return hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()


async def verificar_hmac_evolution(
    request: Request,
    body: bytes = Depends(_leer_cuerpo_raw),
) -> None:
    """
    Dependencia: valida la firma HMAC-SHA256 de Evolution API.

    Evolution API envía la firma en el header:
        x-evolution-signature: sha256=<hex>

    Si EVOLUTION_WEBHOOK_SECRET está vacío, la validación se omite
    (retrocompatible con instalaciones sin secret configurado).
    """
    cfg = obtener_config()

    if not cfg.evolution_webhook_secret:
        # Sin secret configurado → modo dev, sin validación
        logger.debug("HMAC Evolution: secret no configurado, validación omitida.")
        return

    signature_header = (
        request.headers.get("x-evolution-signature")
        or request.headers.get("x-hub-signature-256")
        or ""
    )

    if not signature_header:
        logger.warning("HMAC Evolution: header de firma ausente en la solicitud. Omitiendo validación HMAC para retrocompatibilidad.")
        return

    # Normalizar: quitar prefijo "sha256=" si viene incluido
    received = signature_header.removeprefix("sha256=")
    expected = _calcular_hmac(cfg.evolution_webhook_secret, body)

    if not hmac.compare_digest(received, expected):
        logger.warning("HMAC Evolution: firma inválida. Posible payload manipulado.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma de webhook inválida.",
        )

    logger.debug("HMAC Evolution: firma verificada correctamente.")


async def verificar_hmac_mercadopago(
    request: Request,
    body: bytes = Depends(_leer_cuerpo_raw),
) -> None:
    """
    Dependencia: valida la firma HMAC-SHA256 de MercadoPago.

    MercadoPago envía:
        x-signature: ts=<timestamp>,v1=<hex>
        x-request-id: <uuid>

    Si MP_WEBHOOK_SECRET está vacío, la validación se omite.
    """
    cfg = obtener_config()

    if not cfg.mp_webhook_secret:
        logger.debug("HMAC MercadoPago: secret no configurado, validación omitida.")
        return

    sig_header = request.headers.get("x-signature", "")
    request_id = request.headers.get("x-request-id", "")

    # Parsear ts y v1
    parts = dict(item.split("=", 1) for item in sig_header.split(",") if "=" in item)
    ts = parts.get("ts", "")
    v1 = parts.get("v1", "")

    if not ts or not v1:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Header x-signature inválido o ausente.",
        )

    # Construir el mensaje que MercadoPago firmó: id;ts;body
    data_to_sign = f"{request_id};{ts};{body.decode('utf-8', errors='replace')}"
    expected = _calcular_hmac(cfg.mp_webhook_secret, data_to_sign.encode())

    if not hmac.compare_digest(v1, expected):
        logger.warning("HMAC MercadoPago: firma inválida.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Firma de webhook MercadoPago inválida.",
        )

    logger.debug("HMAC MercadoPago: firma verificada correctamente.")
