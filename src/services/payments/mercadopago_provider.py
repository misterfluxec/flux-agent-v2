import hmac
import hashlib
from typing import Dict, Any
from services.payments.base import PaymentGatewayInterface
from config import obtener_config
settings = obtener_config()

class MercadoPagoProvider(PaymentGatewayInterface):
    async def create_payment_link(self, order_id: str, amount: float, currency: str, description: str, tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        import mercadopago
        
        # En multi-tenant, usaríamos el token guardado en tenant_config. 
        # Por ahora fall back a settings.
        access_token = tenant_config.get("mp_access_token") or getattr(settings, "MP_ACCESS_TOKEN", None)
        if not access_token:
            raise ValueError("MercadoPago access token no configurado para este tenant.")
            
        mp = mercadopago.SDK(access_token)
        
        preference = {
            "items": [{
                "title": description,
                "quantity": 1,
                "unit_price": float(amount),
                "currency_id": currency or "USD"
            }],
            "back_urls": {
                "success": f"{settings.FRONTEND_URL}/operations?payment=success&order_id={order_id}",
                "failure": f"{settings.FRONTEND_URL}/operations?payment=failure",
                "pending": f"{settings.FRONTEND_URL}/operations?payment=pending"
            },
            "auto_return": "approved",
            "notification_url": f"{settings.BACKEND_URL}/api/v1/payments/mp/webhook",
            "external_reference": order_id,
            "metadata": {"order_id": order_id}
        }
        
        result = mp.preference().create(preference)
        response = result.get("response", {})
        
        return {
            "preference_id": response.get("id"),
            "init_point": response.get("init_point"),
            "sandbox_init_point": response.get("sandbox_init_point")
        }

    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str], tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: Implementar validación estricta de firma x-signature aquí.
        # Retornamos el formato normalizado:
        
        # Suponiendo validación exitosa:
        data_id = payload.get("data", {}).get("id")
        if not data_id or payload.get("type") != "payment":
            return {"status": "ignored"}
            
        import mercadopago
        access_token = tenant_config.get("mp_access_token") or getattr(settings, "MP_ACCESS_TOKEN", None)
        mp = mercadopago.SDK(access_token)
        
        payment_info = mp.payment().get(data_id)
        payment = payment_info.get("response", {})
        
        return {
            "status": "approved" if payment.get("status") == "approved" else "rejected",
            "order_id": payment.get("external_reference"),
            "payment_id": str(payment.get("id")),
            "payment_method": payment.get("payment_method_id", "unknown")
        }

    async def refund_payment(self, payment_id: str, amount: float, tenant_config: Dict[str, Any]) -> Dict[str, Any]:
        import mercadopago
        access_token = tenant_config.get("mp_access_token") or getattr(settings, "MP_ACCESS_TOKEN", None)
        mp = mercadopago.SDK(access_token)
        
        result = mp.refund().create(payment_id, {"amount": amount})
        return result.get("response", {})
