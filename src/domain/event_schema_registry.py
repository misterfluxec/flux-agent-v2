from enum import Enum
from typing import Type, Dict, Any, Optional
from pydantic import BaseModel, Field

class EventVersionError(Exception):
    pass

class EventSchemaRegistry:
    """
    Central Registry for deterministic event schemas.
    Garantees that every payload conforms to a known versioned schema before entering the EventBus/Outbox.
    """
    _schemas: Dict[str, Type[BaseModel]] = {}

    @classmethod
    def register(cls, event_type: str, version: str) -> callable:
        """Decorator to register a schema for a specific event type and version"""
        def decorator(schema_cls: Type[BaseModel]):
            key = f"{event_type}@{version}"
            cls._schemas[key] = schema_cls
            return schema_cls
        return decorator

    @classmethod
    def validate_payload(cls, event_type: str, version: str, payload: Dict[str, Any]) -> BaseModel:
        """Validates a payload against its registered schema."""
        key = f"{event_type}@{version}"
        schema_cls = cls._schemas.get(key)
        
        if not schema_cls:
            raise EventVersionError(f"No schema registered for {key}")
            
        return schema_cls.model_validate(payload)

# -------------------------------------------------------------
# Base Schemas
# -------------------------------------------------------------

class BaseEventPayload(BaseModel):
    """Base for all event payloads"""
    pass

# -------------------------------------------------------------
# Core Event Contracts (Examples)
# -------------------------------------------------------------

@EventSchemaRegistry.register("order.created", "v1")
class OrderCreatedV1(BaseEventPayload):
    order_id: str
    customer_id: str
    total_amount: float
    currency: str = "USD"
    items_count: int

@EventSchemaRegistry.register("message.received", "v1")
class MessageReceivedV1(BaseEventPayload):
    message_id: str
    customer_id: str
    channel: str
    content: str
    
@EventSchemaRegistry.register("lead.created", "v1")
class LeadCreatedV1(BaseEventPayload):
    customer_id: str
    source: str
    campaign_id: Optional[str] = None
