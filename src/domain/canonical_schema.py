from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

class CanonicalType(str, Enum):
    """
    Tipos de entidades canónicas soportadas en el OS.
    Toda integración debe traducir hacia estas entidades.
    """
    CATALOG_ITEM = "CatalogItem"
    ORDER = "Order"
    CUSTOMER = "Customer"

class SchemaVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"

class CanonicalCatalogItem(BaseModel):
    """
    Esquema Canónico para un Producto/Servicio en el Catálogo.
    """
    sku: str = Field(..., description="Identificador único (Código/SKU)")
    name: str = Field(..., description="Nombre del producto o servicio")
    price: float = Field(..., description="Precio final de venta")
    stock: int = Field(default=0, description="Cantidad en inventario")
    status: str = Field(default="active", description="Estado operativo (active, draft, out_of_stock)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Datos extra no canónicos")
    schema_version: SchemaVersion = Field(default=SchemaVersion.V1)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CanonicalCustomer(BaseModel):
    """
    Esquema Canónico para un Cliente/Lead.
    """
    customer_id: str
    full_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CanonicalOrder(BaseModel):
    """
    Esquema Canónico para un Pedido de venta.
    """
    order_id: str
    customer_id: str
    total_amount: float
    status: str = Field(default="pending")
    items: list[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class SchemaDriftWarning(Exception):
    """Excepción lanzada cuando una columna mapeada previamente ya no existe en el origen."""
    pass
