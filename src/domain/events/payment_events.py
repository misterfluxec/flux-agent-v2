from pydantic import BaseModel, Field
from typing import Optional
from domain.commerce_states import PaymentStatus
from domain.events.inventory_events import BaseDomainEvent

# ==========================================
# PAYMENT EVENTS (Version 1)
# ==========================================

class PaymentIntentCreatedEventV1(BaseDomainEvent):
    """Emitido cuando se crea la intención de pago para enviar al proveedor."""
    payment_intent_id: str
    order_id: str
    provider: str
    amount: float
    currency: str

class PaymentStatusUpdatedEventV1(BaseDomainEvent):
    """
    Emitido cuando el Payment Reconciliation Engine confirma 
    el cambio de status de un pago (ej. pending -> paid).
    """
    payment_intent_id: str
    order_id: str
    provider: str
    external_transaction_id: str
    previous_status: PaymentStatus
    new_status: PaymentStatus
    amount: float
    error_message: Optional[str] = None
