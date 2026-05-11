from pydantic import BaseModel, Field
from typing import Optional
from domain.commerce_states import InventoryMovementType, InventoryReasonCode, ReservationType

class BaseDomainEvent(BaseModel):
    """Base schema para todos los eventos del sistema."""
    event_id: str
    correlation_id: str
    tenant_id: str
    timestamp: str
    version: str = Field(default="v1")
    source: str

# ==========================================
# INVENTORY EVENTS (Version 1)
# ==========================================

class InventoryMovementEventV1(BaseDomainEvent):
    """
    Emitido cuando el ledger inmutable registra un movimiento (+ o -).
    Ejemplo de topic: inventory.reserved.v1, inventory.committed.v1
    """
    catalog_item_id: str
    movement_type: InventoryMovementType
    reservation_type: Optional[ReservationType] = None
    reason_code: InventoryReasonCode
    quantity: int
    new_available_stock: int
    new_current_stock: int
    new_reserved_stock: int
    ledger_id: str

class InventoryDriftDetectedEventV1(BaseDomainEvent):
    """
    Emitido por el Integrity Worker cuando detecta que el Snapshot 
    no coincide con la suma del Ledger Inmutable.
    """
    catalog_item_id: str
    snapshot_available: int
    ledger_calculated_available: int
    drift_quantity: int
    snapshot_version_number: int

class InventorySnapshotRebuiltEventV1(BaseDomainEvent):
    """
    Emitido cuando el worker repara un snapshot corrupto leyendo todo el Ledger.
    """
    catalog_item_id: str
    previous_available_stock: int
    rebuilt_available_stock: int
    reason: str
