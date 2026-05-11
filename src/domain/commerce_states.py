from typing import Literal, List, Dict
from pydantic import BaseModel, ConfigDict

# ==========================================
# STRICT DOMAIN TYPES (Enums/Literals)
# ==========================================

QuoteStatus = Literal['draft', 'sent', 'viewed', 'accepted', 'expired', 'rejected', 'converted']
OrderStatus = Literal['pending', 'confirmed', 'processing', 'fulfilled', 'cancelled', 'refunded']
PaymentStatus = Literal['pending', 'authorized', 'processing', 'paid', 'failed', 'expired', 'chargeback', 'refunded']
InventoryLockStatus = Literal['reserved', 'allocated', 'deducted', 'released']
InventoryMovementType = Literal['IMPORT', 'RESERVE', 'COMMIT', 'RELEASE', 'ADJUSTMENT', 'RETURN', 'REFUND', 'TRANSFER', 'SYNC_CORRECTION']
InventoryReasonCode = Literal['checkout_pending', 'quote_conversion', 'manual_adjustment', 'erp_sync', 'refund', 'stock_reconciliation', 'abandoned_cart_cleanup']
ReservationType = Literal['soft', 'hard']

# ==========================================
# TRANSITION GRAPHS (State Machines)
# Define desde qué estados se puede pasar a qué estados
# ==========================================

QUOTE_TRANSITIONS: Dict[QuoteStatus, List[QuoteStatus]] = {
    'draft': ['sent', 'accepted', 'rejected'],
    'sent': ['viewed', 'accepted', 'rejected', 'expired'],
    'viewed': ['accepted', 'rejected', 'expired'],
    'accepted': ['converted', 'expired'],  # Debe ser converted a una Order
    'expired': [],
    'rejected': [],
    'converted': []
}

ORDER_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
    'pending': ['confirmed', 'cancelled'],
    'confirmed': ['processing', 'cancelled'],
    'processing': ['fulfilled', 'cancelled'],
    'fulfilled': ['refunded'],
    'cancelled': [],
    'refunded': []
}

PAYMENT_TRANSITIONS: Dict[PaymentStatus, List[PaymentStatus]] = {
    'pending': ['authorized', 'processing', 'paid', 'failed', 'expired'],
    'authorized': ['processing', 'paid', 'failed', 'expired'],
    'processing': ['paid', 'failed'],
    'paid': ['chargeback', 'refunded'],
    'failed': ['pending'], # Retry
    'expired': [],
    'chargeback': [],
    'refunded': []
}

INVENTORY_LOCK_TRANSITIONS: Dict[InventoryLockStatus, List[InventoryLockStatus]] = {
    'reserved': ['allocated', 'released'], # Reservado en carrito temporalmente
    'allocated': ['deducted', 'released'], # Asignado (pago en proceso)
    'deducted': ['released'], # Stock descontado definitivamente
    'released': [] # Reserva liberada, stock vuelve a pool
}

class InvalidStateTransitionError(Exception):
    pass

class CommerceStateValidator:
    """Validador estricto de State Machines Comerciales"""
    
    @staticmethod
    def validate_quote_transition(current: QuoteStatus, new: QuoteStatus):
        if new not in QUOTE_TRANSITIONS.get(current, []):
            raise InvalidStateTransitionError(f"Cannot transition Quote from {current} to {new}")
            
    @staticmethod
    def validate_order_transition(current: OrderStatus, new: OrderStatus):
        if new not in ORDER_TRANSITIONS.get(current, []):
            raise InvalidStateTransitionError(f"Cannot transition Order from {current} to {new}")
            
    @staticmethod
    def validate_payment_transition(current: PaymentStatus, new: PaymentStatus):
        if new not in PAYMENT_TRANSITIONS.get(current, []):
            raise InvalidStateTransitionError(f"Cannot transition Payment from {current} to {new}")

    @staticmethod
    def validate_inventory_lock_transition(current: InventoryLockStatus, new: InventoryLockStatus):
        if new not in INVENTORY_LOCK_TRANSITIONS.get(current, []):
            raise InvalidStateTransitionError(f"Cannot transition Inventory Lock from {current} to {new}")
