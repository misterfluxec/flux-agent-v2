# ERP Connector Framework — FluxAgent V2
from .v2.base_connector import BaseDataConnector as ERPConnectorInterface
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
