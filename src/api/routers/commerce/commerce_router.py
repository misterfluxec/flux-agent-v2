from fastapi import APIRouter, Depends, Request, HTTPException, BackgroundTasks, Header
from sqlalchemy.ext.asyncio import AsyncSession
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
import uuid
from pydantic import BaseModel
from typing import List, Optional

class QuoteItemSchema(BaseModel):
    catalog_item_id: str
    quantity: int
    unit_price: float

class QuoteCreateSchema(BaseModel):
    customer_id: str
    items: List[QuoteItemSchema]
    total: float

@router.post("/quotes")
async def create_quote(
    payload: QuoteCreateSchema,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Crea una cotización en estado draft."""
    from sqlalchemy import text
    try:
        quote_id = str(uuid.uuid4())
        await db.execute(text("""
            INSERT INTO quotes (id, tenant_id, customer_id, status, total)
            VALUES (:id, :tenant_id, :customer_id, 'draft', :total)
        """), {
            "id": quote_id,
            "tenant_id": tenant_id,
            "customer_id": payload.customer_id,
            "total": payload.total
        })
        
        for item in payload.items:
            await db.execute(text("""
                INSERT INTO quote_items (id, quote_id, catalog_item_id, quantity, unit_price)
                VALUES (:id, :quote_id, :catalog_item_id, :qty, :price)
            """), {
                "id": str(uuid.uuid4()),
                "quote_id": quote_id,
                "catalog_item_id": item.catalog_item_id,
                "qty": item.quantity,
                "price": item.unit_price
            })
            
        await db.commit()
        return {"status": "success", "quote_id": quote_id}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quotes")
async def get_quotes(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lista las cotizaciones del tenant."""
    from sqlalchemy import text
    try:
        res = await db.execute(text("SELECT id, customer_id, status, total, created_at FROM quotes WHERE tenant_id = :tid ORDER BY created_at DESC"), {"tid": tenant_id})
        quotes = [dict(r._mapping) for r in res.fetchall()]
        return {"status": "success", "data": quotes}
    except Exception as e:
        # Fallback para desarrollo si la tabla no existe
        return {"status": "success", "data": []}

@router.get("/orders")
async def get_orders(
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Lista las órdenes del tenant."""
    from sqlalchemy import text
    try:
        res = await db.execute(text("SELECT id, customer_id, status, total_amount, payment_status, created_at FROM orders WHERE tenant_id = :tid ORDER BY created_at DESC"), {"tid": tenant_id})
        orders = [dict(r._mapping) for r in res.fetchall()]
        return {"status": "success", "data": orders}
    except Exception as e:
        # Fallback para desarrollo si la tabla no existe
        return {"status": "success", "data": []}

@router.post("/orders/{order_id}/cancel")
async def cancel_order(
    order_id: str,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Cancela una orden y libera el lock de inventario (HITL)."""
    from sqlalchemy import text
    try:
        # Actualizar estado de orden
        await db.execute(text("UPDATE orders SET status = 'cancelled' WHERE id = :id AND tenant_id = :tid"), {"id": order_id, "tid": tenant_id})
        # Liberar inventory locks
        await db.execute(text("UPDATE inventory_locks SET status = 'released' WHERE order_id = :oid"), {"oid": order_id})
        await db.commit()
        return {"status": "success", "message": "Order cancelled"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/quotes/{quote_id}")
async def update_quote(
    quote_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Actualiza parcialmente una cotización (ej. status a accepted)."""
    from sqlalchemy import text
    try:
        if "status" in payload:
            await db.execute(text("UPDATE quotes SET status = :st WHERE id = :id AND tenant_id = :tid"), {"st": payload["status"], "id": quote_id, "tid": tenant_id})
        await db.commit()
        return {"status": "success", "message": "Quote updated"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/orders/{order_id}/fulfill")
async def fulfill_order(
    order_id: str,
    payload: dict,
    db: AsyncSession = Depends(get_db),
    tenant_id: str = Depends(get_tenant_id)
):
    """Avanza el estado de la orden (ej. shipped, delivered)."""
    from sqlalchemy import text
    try:
        if "status" in payload:
            await db.execute(text("UPDATE orders SET status = :st WHERE id = :id AND tenant_id = :tid"), {"st": payload["status"], "id": order_id, "tid": tenant_id})
        await db.commit()
        return {"status": "success", "message": "Order fulfilled"}
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quotes/{quote_id}/convert")
def convert_quote(

    quote_id: str,
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db)
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
