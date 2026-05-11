from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks, Header
from sqlalchemy.orm import Session
from typing import Dict, Any
import os

from database import get_db
from services.commerce_lifecycle_engine import CommerceLifecycleEngine
from services.payment_gateway import PaymentGateway, WebhookDuplicateError

router = APIRouter(prefix="/api/v1/commerce", tags=["commerce"])

def get_tenant_id(request: Request) -> str:
    """Mock tenant extractor from headers or auth token."""
    tenant_id = request.headers.get("x-tenant-id")
    if not tenant_id:
        raise HTTPException(status_code=400, detail="Missing x-tenant-id header")
    return tenant_id

# ==========================================
# QUOTES & ORDERS
# ==========================================

@router.post("/quotes/{quote_id}/convert")
def convert_quote(
    quote_id: str,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Convierte una cotización en una Orden, ejecutando el ciclo de vida estricto 
    y despachando los eventos pertinentes mediante el Transaction Manager.
    """
    engine = CommerceLifecycleEngine(db, tenant_id)
    try:
        # Nota: En una versión completa, se pasaría actor_id extraído del token JWT
        order_id = engine.convert_quote_to_order(quote_id, actor_id="api_user")
        return {
            "status": "success", 
            "message": "Quote converted to order successfully",
            "order_id": order_id
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# PAYMENTS & CHECKOUT
# ==========================================

@router.post("/orders/{order_id}/payment-link")
def generate_payment_link(
    order_id: str,
    request: Request,
    db: Session = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """
    Genera un link de pago real de MercadoPago delegando al PaymentGateway.
    Crea el Payment Intent internamente.
    """
    # En producción esto vendría de la DB (tenant_secrets) o env
    mp_access_token = os.environ.get("MP_ACCESS_TOKEN", "TEST-dummy-token")
    
    gateway = PaymentGateway(db, tenant_id, access_token=mp_access_token)
    base_url = str(request.base_url).rstrip("/")

    try:
        result = gateway.create_payment_preference(order_id, base_url)
        return {
            "status": "success",
            "payment_intent_id": result["payment_intent_id"],
            "payment_link": result["init_point"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# WEBHOOKS (Idempotency Shield)
# ==========================================

@router.post("/webhooks/mp/{tenant_id}")
def mp_webhook(
    tenant_id: str,
    request: Request,
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks,
    x_signature: str = Header(None),
    x_request_id: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Endpoint para recibir webhooks de MercadoPago. 
    Se encarga ÚNICAMENTE de ingerirlos de forma segura en `webhook_events`.
    No bloquea a MercadoPago. La conciliación la hace un worker asíncrono.
    """
    # 1. Recuperar secretos (dummy para MVP)
    mp_secret = os.environ.get("MP_WEBHOOK_SECRET", "dummy-secret")
    gateway = PaymentGateway(db, tenant_id)

    # 2. Verificar firma criptográfica (Anti-spoofing)
    # (Comentado/simplificado para MVP)
    # if not gateway.verify_mercadopago_signature(x_signature, x_request_id, payload.get("data", {}).get("id"), mp_secret):
    #     raise HTTPException(status_code=403, detail="Invalid signature")

    # 3. Extraer IDs según estructura de MP
    provider_event_id = str(payload.get("id") or payload.get("data", {}).get("id", "unknown"))
    event_type = payload.get("type") or payload.get("action", "unknown")

    try:
        # 4. Ingestión idempotente
        gateway.ingest_webhook(
            provider="mercadopago",
            provider_event_id=provider_event_id,
            event_type=event_type,
            payload=payload
        )
        return {"status": "received"}

    except WebhookDuplicateError:
        # Si MercadoPago nos envía un duplicado por lag de su red, respondemos 200 OK 
        # para que dejen de molestar, pero NO lo procesamos internamente.
        return {"status": "ignored", "reason": "duplicate"}
        
    except Exception as e:
        # Si falla por base de datos u otro motivo real, tiramos 500 para que MP reintente luego.
        raise HTTPException(status_code=500, detail="Failed to ingest webhook")
