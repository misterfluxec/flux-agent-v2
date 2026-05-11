# =============================================================================
# FLUXAGENT V2 — CANONICAL BUSINESS MODEL
# =============================================================================
# Modelos de datos universales que actúan como capa de traducción entre
# cualquier ERP externo y el esquema interno de FluxAgent (catalog_items,
# orders, quotes).
#
# ERP (SAP / Odoo / SQL Server / Siigo) → Canonical → FluxAgent Tables
#
# Estos modelos NUNCA se persisten directamente. Son DTOs de transporte
# que el Sync Engine transforma en INSERTs/UPSERTs sobre las tablas
# existentes de commerce_core.
# =============================================================================

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field
from enum import StrEnum


class SyncDirection(StrEnum):
    IMPORT = "import"       # ERP → FluxAgent
    EXPORT = "export"       # FluxAgent → ERP
    BIDIRECTIONAL = "bidi"  # Ambas direcciones


class CanonicalProduct(BaseModel):
    """Representación universal de un producto/servicio importado desde un ERP."""
    external_id: str = Field(description="ID original en el sistema ERP fuente")
    sku: Optional[str] = None
    name: str
    description: Optional[str] = None
    price: float = Field(ge=0)
    cost: Optional[float] = Field(default=None, ge=0)
    currency: str = "USD"
    category: Optional[str] = None
    brand: Optional[str] = None
    item_type: str = "physical_product"  # Mapea a catalog_items.type
    is_active: bool = True
    metadata: dict = Field(default_factory=dict)


class CanonicalInventory(BaseModel):
    """Estado de inventario de un producto en un almacén específico."""
    external_product_id: str
    sku: Optional[str] = None
    warehouse_id: Optional[str] = None
    warehouse_name: Optional[str] = None
    stock_available: int = Field(ge=0)
    stock_reserved: int = Field(default=0, ge=0)
    low_stock_threshold: int = Field(default=5, ge=0)
    last_updated: Optional[datetime] = None


class CanonicalCustomer(BaseModel):
    """Representación universal de un cliente/contacto."""
    external_id: str
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    document_type: Optional[str] = None  # RUC, CI, NIT, RFC, CUIT
    document_number: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    credit_status: Optional[str] = None  # active, blocked, credit_hold
    credit_limit: Optional[float] = None
    metadata: dict = Field(default_factory=dict)


class CanonicalOrderItem(BaseModel):
    """Línea individual de una orden importada."""
    external_product_id: str
    sku: Optional[str] = None
    product_name: str
    quantity: int = Field(ge=1)
    unit_price: float = Field(ge=0)
    discount_percent: float = Field(default=0, ge=0, le=100)


class CanonicalOrder(BaseModel):
    """Representación universal de una orden/pedido importado."""
    external_id: str
    external_customer_id: Optional[str] = None
    status: str = "pending"
    items: List[CanonicalOrderItem] = Field(default_factory=list)
    subtotal: float = Field(ge=0)
    tax_amount: float = Field(default=0, ge=0)
    total: float = Field(ge=0)
    currency: str = "USD"
    payment_method: Optional[str] = None
    payment_status: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)


class SyncResult(BaseModel):
    """Resultado de una operación de sincronización."""
    connector_type: str
    direction: SyncDirection
    entity_type: str  # "product", "customer", "order", "inventory"
    total_fetched: int = 0
    inserted: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0
    error_details: List[str] = Field(default_factory=list)
    duration_ms: int = 0
    synced_at: datetime = Field(default_factory=datetime.utcnow)
