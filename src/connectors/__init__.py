# ERP Connector Framework — FluxAgent V2
from .legacy.base import ERPConnectorInterface
from .canonical import (
    CanonicalProduct,
    CanonicalCustomer,
    CanonicalOrder,
    CanonicalOrderItem,
    CanonicalInventory,
    SyncResult,
)

__all__ = [
    "ERPConnectorInterface",
    "CanonicalProduct",
    "CanonicalCustomer",
    "CanonicalOrder",
    "CanonicalOrderItem",
    "CanonicalInventory",
    "SyncResult",
]
