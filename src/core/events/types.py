"""
Core Events Types — FluxAgent V2
Defines Event, EventType and related structures for the event bus.
"""
from enum import Enum
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid


class EventType(str, Enum):
    # Conversation events
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_CLOSED = "conversation.closed"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    HANDOFF_REQUESTED = "handoff.requested"
    HANDOFF_COMPLETED = "handoff.completed"

    # Agent events
    AGENT_RESPONSE = "agent.response"
    AGENT_ERROR = "agent.error"
    AGENT_STARTED = "agent.started"
    AGENT_STOPPED = "agent.stopped"

    # Task events
    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_STEP_STARTED = "task.step.started"
    TASK_STEP_COMPLETED = "task.step.completed"
    TASK_STEP_FAILED = "task.step.failed"

    # System events
    SYSTEM_ALERT = "system.alert"
    SYSTEM_HEALTH = "system.health"
    TENANT_QUOTA_WARNING = "tenant.quota.warning"

    # Commerce events
    ORDER_CREATED = "order.created"
    PAYMENT_RECEIVED = "payment.received"
    QUOTE_APPROVED = "quote.approved"


@dataclass
class Event:
    """Standard event envelope for the FluxAgent event bus."""
    type: EventType
    payload: Dict[str, Any] = field(default_factory=dict)
    tenant_id: Optional[str] = None
    channel: Optional[str] = None
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "type": self.type.value if isinstance(self.type, EventType) else self.type,
            "payload": self.payload,
            "tenant_id": self.tenant_id,
            "channel": self.channel,
            "timestamp": self.timestamp,
        }
