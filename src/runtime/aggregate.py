from typing import List, Dict, Any, Optional
import logging
from .event_store import StoredEvent

logger = logging.getLogger(__name__)

class AggregateRoot:
    """
    Base class for Domain Aggregates.
    Reconstruye el estado del dominio reproduciendo los eventos almacenados.
    """
    
    def __init__(self, aggregate_id: str):
        self.aggregate_id = aggregate_id
        self.version = 0
        self._uncommitted_events: List[StoredEvent] = []

    def apply(self, event: StoredEvent):
        """
        Aplica un evento al estado actual y actualiza la versión.
        Busca un método `_apply_{event_type}` en la subclase.
        """
        method_name = f"_apply_{event.event_type.lower()}"
        applier = getattr(self, method_name, None)
        
        if applier:
            applier(event.payload, event.schema_version)
        else:
            logger.debug(f"[{self.__class__.__name__}] Ignorado evento sin manejador: {event.event_type}")

        self.version = event.version

    def load_from_events(self, events: List[StoredEvent]):
        """Reconstruye el estado aplicando una historia de eventos secuencialmente."""
        for event in events:
            self.apply(event)

    def load_from_snapshot(self, snapshot: Dict[str, Any], events_after: List[StoredEvent]):
        """Opcional: Reconstruye desde un snapshot + eventos posteriores."""
        # Se debe implementar en las subclases según sus atributos
        pass

class OrderAggregate(AggregateRoot):
    """
    Ejemplo de un Aggregate para gestionar Órdenes.
    """
    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id)
        self.status = "NONE"
        self.items = []
        self.total = 0.0
        self.payment_status = "PENDING"
        
    def _apply_ordercreated(self, payload: Dict[str, Any], schema_version: int):
        self.status = "CREATED"
        if schema_version >= 2:
            self.items = payload.get("line_items", [])
            self.total = payload.get("grand_total", 0.0)
        else:
            self.items = payload.get("items", [])
            self.total = payload.get("total", 0.0)

    def _apply_orderpaid(self, payload: Dict[str, Any], schema_version: int):
        self.payment_status = "PAID"
        if payload.get("amount_paid", 0.0) >= self.total:
            self.status = "PROCESSING"

    def _apply_ordercancelled(self, payload: Dict[str, Any], schema_version: int):
        self.status = "CANCELLED"
        self.payment_status = "REFUNDED" if self.payment_status == "PAID" else "CANCELLED"
