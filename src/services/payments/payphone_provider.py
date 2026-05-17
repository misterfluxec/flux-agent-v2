import httpx
import logging
from typing import Dict, Any
from services.payments.base import PaymentGatewayInterface

logger = logging.getLogger(__name__)

class PayPhoneProvider(PaymentGatewayInterface):
    """
    Integración con PayPhone Ecuador.
    Soporta pagos en USD.
    """
    BASE_URL = "https://pay.payphonetodoesposible.com/api"

    async def create_payment_link(
        self, order_id: str, amount: float, currency: str, description: str, tenant_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Crea un botón de pago en PayPhone.
        """
        if currency.upper() != "USD":
            raise ValueError("PayPhone Ecuador solo soporta USD.")

        # Payphone maneja montos en centavos (int)
        amount_cents = int(amount * 100)

        token = tenant_config.get("payphone_token")
        if not token:
            raise ValueError("Token de PayPhone no configurado para este Tenant.")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # Configurar URLs de retorno (se asume que el webhook config viene en tenant_config)
        webhook_base_url = tenant_config.get("webhook_base_url", "https://api.labodegaec.com/api/v1/webhooks/payphone")

        payload = {
            "amount": amount_cents,
            "amountWithoutTax": amount_cents,
            "amountWithTax": 0,
            "tax": 0,
            "clientTransactionId": str(order_id),
            "currency": "USD",
            "reference": description[:50],  # Limitar longitud
            "responseUrl": f"{webhook_base_url}/return",
            "cancellationUrl": f"{webhook_base_url}/cancel"
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{self.BASE_URL}/button/Prepare",
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                resp.raise_for_status()
                data = resp.json()

                # PayPhone retorna 'paymentId'
                payment_id = data.get("paymentId")
                
                # Para mostrar el widget o redireccionar, PayPhone normalmente se integra con su JS,
                # pero si hay una URL de checkout directa se retorna. Si no, se retorna el paymentId.
                # Documentación estándar: Se usa https://pay.payphonetodoesposible.com/PayPhone/Checkout?paymentId=...
                init_point = f"https://pay.payphonetodoesposible.com/PayPhone/Checkout?paymentId={payment_id}"

                return {
                    "init_point": init_point,
                    "payment_id": payment_id,
                    "raw_response": data
                }

        except httpx.HTTPStatusError as e:
            logger.error(f"Error HTTP en PayPhone: {e.response.text}")
            raise Exception(f"Fallo al crear pago en PayPhone: {e.response.status_code}")
        except Exception as e:
            logger.error(f"Error de conexión con PayPhone: {str(e)}")
            raise

    async def process_webhook(
        self, payload: Dict[str, Any], headers: Dict[str, str], tenant_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PayPhone envía un webhook (IPN) cuando el status cambia.
        Normalmente envía 'id' y 'clientTxId' y requiere que consultemos el status real.
        """
        payment_id = payload.get("id")
        client_txn_id = payload.get("clientTxId")

        if not payment_id:
            raise ValueError("Payload de PayPhone inválido: Falta 'id'")

        # Consultar status real del pago para evitar fraudes
        token = tenant_config.get("payphone_token")
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/button/{payment_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            resp.raise_for_status()
            data = resp.json()

        # data["transactionStatus"] -> "Approved", "Canceled", "Pending"
        status_raw = data.get("transactionStatus", "").upper()

        status_mapped = "pending"
        if status_raw == "APPROVED":
            status_mapped = "approved"
        elif status_raw in ["CANCELED", "REJECTED"]:
            status_mapped = "rejected"

        return {
            "status": status_mapped,
            "order_id": str(client_txn_id) if client_txn_id else None,
            "payment_id": str(payment_id),
            "payment_method": data.get("cardType", "credit_card"),
            "raw_payload": data
        }

    async def refund_payment(
        self, payment_id: str, amount: float, tenant_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Anulación en PayPhone (Annul).
        """
        token = tenant_config.get("payphone_token")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "id": int(payment_id) if payment_id.isdigit() else payment_id
        }
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/Annul",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()

        return {
            "status": "refunded",
            "refund_id": str(data.get("transactionId", "")),
            "raw_response": data
        }
