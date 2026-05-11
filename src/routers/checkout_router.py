from fastapi import APIRouter, Request, Header, Depends, HTTPException
from typing import Dict, Any
import logging

from database import obtener_sesion
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from core.event_bus import EventBus
from core.dependencies import get_event_bus
from domain.events import DomainEvent, EventMetadata, EventType, PaymentCompletedPayload, PaymentFailedPayload
from services.payments.payment_factory import PaymentFactory

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/checkout", tags=["checkout"])

@router.post("/{provider}/create")
async def create_payment_link(
    provider: str,
    order_id: str,
    amount: float,
    currency: str = "USD",
    description: str = "Pago de Orden",
    # TODO: Auth/Tenant config cuando esté securizado 
):
    try:
        gateway = PaymentFactory.get_provider(provider)
        
        # Configuración por defecto por ahora
        tenant_config = {}
        
        res = await gateway.create_payment_link(order_id, amount, currency, description, tenant_config)
        return res
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creando pago {provider}: {e}")
        raise HTTPException(status_code=500, detail="Error interno creando pago")

@router.post("/{provider}/webhook")
async def payment_webhook(
    provider: str,
    request: Request,
    x_signature: str = Header(None, alias="x-signature"),
    x_request_id: str = Header(None, alias="x-request-id"),
    db: AsyncSession = Depends(obtener_sesion),
    event_bus: EventBus = Depends(get_event_bus)
):
    try:
        payload = await request.json()
    except Exception:
        payload = {}
        
    headers = {"x-signature": x_signature, "x-request-id": x_request_id}
    
    try:
        gateway = PaymentFactory.get_provider(provider)
    except ValueError:
        return {"status": "ignored", "reason": "unknown_provider"}
        
    tenant_config = {}
    
    result = await gateway.process_webhook(payload, headers, tenant_config)
    
    status = result.get("status")
    if status in ["ignored", "rejected"]:
        return {"status": "processed", "result": status}
        
    order_id = result.get("order_id")
    if not order_id:
        return {"status": "processed", "result": "missing_order_id"}

    # Obtener orden para idempotencia
    query = text("SELECT id, tenant_id, payment_status, total_amount, payment_method FROM orders WHERE id = :order_id")
    order_row = (await db.execute(query, {"order_id": order_id})).mappings().first()
    
    if not order_row:
        return {"status": "processed", "result": "order_not_found"}
        
    if order_row["payment_status"] == status:
        return {"status": "processed", "result": "idempotent"}
        
    # Update orden
    await db.execute(text("""
        UPDATE orders 
        SET payment_status = :status, payment_id = :payment_id, payment_method = :payment_method, status = :new_status
        WHERE id = :order_id
    """), {
        "status": status,
        "payment_id": result.get("payment_id"),
        "payment_method": result.get("payment_method"),
        "new_status": "paid" if status == "approved" else "pending",
        "order_id": order_id
    })
    await db.commit()
    
    # Publish Event
    event_type = EventType.PAYMENT_COMPLETED if status == "approved" else EventType.PAYMENT_FAILED
    
    if status == "approved":
        payload_obj = PaymentCompletedPayload(
            order_id=str(order_id),
            amount=float(order_row["total_amount"]),
            method=result.get("payment_method", "unknown"),
            old_status=order_row["payment_status"] or "pending"
        )
    else:
        payload_obj = PaymentFailedPayload(
            order_id=str(order_id),
            reason=result.get("status", "unknown")
        )
        
    event = DomainEvent(
        metadata=EventMetadata(event_type=event_type, tenant_id=order_row["tenant_id"]),
        payload=payload_obj
    )
    
    await event_bus.publish(event)
    
    return {"status": "processed", "result": "updated_and_published"}
