import hmac
import hashlib
import json
import uuid
from typing import Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from domain.commerce_states import PaymentStatus
import mercadopago

class PaymentGatewayException(Exception):
    pass

class WebhookDuplicateError(Exception):
    """Lanzado cuando MercadoPago re-envía un webhook que ya recibimos."""
    pass

class PaymentGateway:
    """
    Abstracción de Pasarelas de Pago.
    Sprint 3.5: SDK Real de MercadoPago + Ingestión Segura
    """
    def __init__(self, db: Session, tenant_id: str, access_token: str = ""):
        self.db = db
        self.tenant_id = tenant_id
        # Inicializar el SDK real de MercadoPago
        self.sdk = mercadopago.SDK(access_token) if access_token else None

    def create_payment_preference(self, order_id: str, base_url: str) -> Dict[str, Any]:
        """
        Crea una preferencia de pago en MercadoPago y devuelve el Init Point (Checkout URL).
        También registra el Payment Intent interno.
        """
        if not self.sdk:
            raise PaymentGatewayException("MercadoPago access_token is missing for this tenant.")

        # 1. Recuperar info básica de la orden (Subtotal, Currency, etc)
        order_q = text("SELECT subtotal, tax_amount, total_amount, currency FROM orders WHERE id = :id AND tenant_id = :tenant")
        order = self.db.execute(order_q, {"id": order_id, "tenant": self.tenant_id}).fetchone()
        
        if not order:
            raise PaymentGatewayException("Order not found or access denied.")

        # Generar un Idempotency Key único para nosotros
        idempotency_key = f"pi_mp_{uuid.uuid4().hex[:12]}"

        # 2. Registrar el Payment Intent
        pi_id = str(uuid.uuid4())
        self.db.execute(text("""
            INSERT INTO payment_intents (id, tenant_id, order_id, external_provider, amount, currency, status, idempotency_key)
            VALUES (:id, :t, :oid, 'mercadopago', :amt, :curr, 'pending', :ikey)
        """), {
            "id": pi_id, "t": self.tenant_id, "oid": order_id, 
            "amt": order.total_amount, "curr": order.currency, "ikey": idempotency_key
        })
        self.db.commit()

        # 3. Payload para MercadoPago
        preference_data = {
            "items": [
                {
                    "title": f"Orden #{str(order_id)[:8]}",
                    "quantity": 1,
                    "unit_price": float(order.total_amount),
                    "currency_id": order.currency or "USD"
                }
            ],
            "back_urls": {
                "success": f"{base_url}/checkout/success?order_id={order_id}",
                "failure": f"{base_url}/checkout/failure?order_id={order_id}",
                "pending": f"{base_url}/checkout/pending?order_id={order_id}"
            },
            "auto_return": "approved",
            "notification_url": f"{base_url}/api/v1/commerce/webhooks/mp/{self.tenant_id}",
            "external_reference": str(pi_id) # Mandamos el ID del Intent, NO de la Orden, para mayor seguridad
        }

        # 4. Llamar al SDK de MercadoPago
        response = self.sdk.preference().create(preference_data)
        
        if response["status"] not in [200, 201]:
            raise PaymentGatewayException(f"MP Error: {response.get('response')}")

        init_point = response["response"]["init_point"]
        mp_preference_id = response["response"]["id"]

        # Actualizamos el external_transaction_id en nuestro intent con el Preference ID (opcional)
        # o esperamos al Webhook para llenarlo con el Payment ID real.
        self.db.execute(text("UPDATE payment_intents SET external_transaction_id = :pref_id WHERE id = :id"),
                        {"pref_id": mp_preference_id, "id": pi_id})
        self.db.commit()

        return {
            "payment_intent_id": pi_id,
            "init_point": init_point,
            "preference_id": mp_preference_id
        }

    def verify_mercadopago_signature(self, x_signature: str, x_request_id: str, data_id: str, secret: str) -> bool:
        """Validación criptográfica (Omitida en MVP, asume válida)"""
        return True

    def ingest_webhook(self, provider: str, provider_event_id: str, event_type: str, payload: Dict[str, Any]) -> str:
        """
        Guarda el evento crudo de forma idempotente en webhook_events.
        """
        try:
            result = self.db.execute(text("""
                INSERT INTO webhook_events (tenant_id, provider, provider_event_id, event_type, payload, status)
                VALUES (:tenant_id, :provider, :event_id, :event_type, :payload, 'pending')
                RETURNING id
            """), {
                "tenant_id": self.tenant_id,
                "provider": provider,
                "event_id": provider_event_id,
                "event_type": event_type,
                "payload": json.dumps(payload)
            })
            self.db.commit()
            return str(result.fetchone()[0])
            
        except Exception as e:
            self.db.rollback()
            if "unique_provider_event" in str(e).lower():
                raise WebhookDuplicateError(f"Webhook {provider_event_id} from {provider} is already ingested.")
            raise PaymentGatewayException(f"Failed to ingest webhook: {str(e)}")
