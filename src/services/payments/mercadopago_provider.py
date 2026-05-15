import hmac
import hashlib
import time
import logging
from typing import Dict, Any

from services.payments.base import PaymentGatewayInterface
from config import obtener_config
from core.exceptions import WebhookValidationError

logger = logging.getLogger(__name__)


def _validate_mp_signature(
    x_signature: str,
    x_request_id: str,
    data_id: str,
    webhook_secret: str,
) -> None:
    """
    Valida la firma x-signature de MercadoPago (HMAC-SHA256).
    Docs: https://mercadopago.com/developers/es/docs/notifications

    Si webhook_secret está vacío (dev/local), la validación se omite.
    En producción MP_WEBHOOK_SECRET debe estar configurado.
    """
    if not webhook_secret:
        return  # sin secret configurado = solo dev/local

    # Construir el manifest que MP firma
    manifest = f"id:{data_id};request-id:{x_request_id};"

    expected = hmac.new(
        webhook_secret.encode(),
        manifest.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Extraer ts y v1 del header "ts=....,v1=...."
    parts = dict(
        part.split("=", 1)
        for part in x_signature.split(",")
        if "=" in part
    )
    received = parts.get("v1", "")
    ts = int(parts.get("ts", "0") or 0)

    # Anti-replay: rechazar si el webhook tiene más de 5 min
    if abs(time.time() - ts) > 300:
        raise WebhookValidationError(
            "Webhook timestamp fuera de ventana (>5 min)"
        )

    if not hmac.compare_digest(expected, received):
        raise WebhookValidationError(
            "Firma x-signature de MercadoPago inválida"
        )


class MercadoPagoProvider(PaymentGatewayInterface):

    async def create_payment_link(
        self,
        order_id: str,
        amount: float,
        currency: str,
        description: str,
        tenant_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        import mercadopago

        settings = obtener_config()
        # En multi-tenant, usaríamos el token guardado en tenant_config.
        access_token = (
            tenant_config.get("mp_access_token")
            or settings.mp_access_token
        )
        if not access_token:
            raise ValueError("MercadoPago access token no configurado para este tenant.")

        mp = mercadopago.SDK(access_token)

        preference = {
            "items": [{
                "title": description,
                "quantity": 1,
                "unit_price": float(amount),
                "currency_id": currency or "USD",
            }],
            "back_urls": {
                "success": f"{settings.frontend_url}/operations?payment=success&order_id={order_id}",
                "failure": f"{settings.frontend_url}/operations?payment=failure",
                "pending": f"{settings.frontend_url}/operations?payment=pending",
            },
            "auto_return": "approved",
            "notification_url": f"{settings.backend_url}/api/v1/payments/webhook/mercadopago",
            "external_reference": order_id,
            "metadata": {"order_id": order_id},
        }

        result = mp.preference().create(preference)
        response = result.get("response", {})

        return {
            "preference_id": response.get("id"),
            "init_point": response.get("init_point"),
            "sandbox_init_point": response.get("sandbox_init_point"),
        }

    async def process_webhook(
        self,
        payload: Dict[str, Any],
        headers: Dict[str, str],
        tenant_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        settings = obtener_config()

        # Validar firma HMAC antes de procesar
        data_id = str(payload.get("data", {}).get("id", ""))
        _validate_mp_signature(
            x_signature=headers.get("x-signature", ""),
            x_request_id=headers.get("x-request-id", ""),
            data_id=data_id,
            webhook_secret=settings.mp_webhook_secret,
        )

        if not data_id or payload.get("type") != "payment":
            return {"status": "ignored"}

        import mercadopago
        access_token = (
            tenant_config.get("mp_access_token")
            or settings.mp_access_token
        )
        mp = mercadopago.SDK(access_token)

        payment_info = mp.payment().get(data_id)
        payment = payment_info.get("response", {})

        return {
            "status": "approved" if payment.get("status") == "approved" else "rejected",
            "order_id": payment.get("external_reference"),
            "payment_id": str(payment.get("id")),
            "payment_method": payment.get("payment_method_id", "unknown"),
        }

    async def refund_payment(
        self,
        payment_id: str,
        amount: float,
        tenant_config: Dict[str, Any],
    ) -> Dict[str, Any]:
        import mercadopago

        settings = obtener_config()
        access_token = (
            tenant_config.get("mp_access_token")
            or settings.mp_access_token
        )
        mp = mercadopago.SDK(access_token)

        result = mp.refund().create(payment_id, {"amount": amount})
        return result.get("response", {})
