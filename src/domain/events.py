from enum import StrEnum, auto
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any, Union


class EventType(StrEnum):
    # Conversaciones
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_SENT = "message.sent"
    CONVERSATION_STARTED = "conversation.started"
    CONVERSATION_CLOSED = "conversation.closed"
    
    # Leads y CRM
    LEAD_CREATED = "lead.created"
    LEAD_QUALIFIED = "lead.qualified"
    LEAD_SCORE_UPDATED = "lead.score_updated"
    
    # IA y Agentes
    INTENT_DETECTED = "intent.detected"
    AGENT_RESPONSE_GENERATED = "agent.response_generated"
    HANDOFF_REQUESTED = "handoff.requested"
    HANDOFF_COMPLETED = "handoff.completed"
    
    # Canales
    CHANNEL_CONNECTED = "channel.connected"
    CHANNEL_DISCONNECTED = "channel.disconnected"
    QR_CODE_UPDATED = "qr_code.updated"
    
    # Alertas y Notificaciones
    ALERT_IA_DETECTED = "alert.ia_detected"
    ALERT_URGENT = "alert.urgent"
    
    # Sistema
    TENANT_USAGE_UPDATED = "tenant.usage_updated"
    BILLING_THRESHOLD_REACHED = "billing.threshold_reached"

    # Voz / Pipecat
    VOICE_CALL_STARTED = "voice.call_started"
    VOICE_TRANSCRIPTION_CHUNK = "voice.transcription_chunk"
    AGENT_INTERRUPTED = "agent.interrupted"
    SILENCE_DETECTED = "voice.silence_detected"
    VOICE_CALL_ENDED = "voice.call_ended"

    # Orchestrator & Policies
    ORCHESTRATOR_STARTED = "orchestrator.started"
    ORCHESTRATOR_STEP_COMPLETED = "orchestrator.step_completed"

    # Commerce & Ops
    QUOTE_GENERATED = "quote.generated"
    QUOTE_ACCEPTED = "quote.accepted"
    QUOTE_EXPIRED = "quote.expired"
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_FULFILLED = "order.fulfilled"
    BOOKING_CONFIRMED = "booking.confirmed"
    BOOKING_CANCELLED = "booking.cancelled"
    FOLLOWUP_SCHEDULED = "followup.scheduled"
    SLA_RISK = "sla.risk"
    LEAD_HOT = "lead.hot"
    POLICY_VIOLATION = "policy.violation"
    TOOL_EXECUTED = "tool.executed"
    RESPONSE_GENERATED = "response.generated"

    # Billing & Usage
    BILLING_ALERT = "billing.alert"
    TENANT_QUOTA_EXHAUSTED = "tenant.quota_exhausted"

    # Pagos y Commerce
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"

    # ERP Connector Framework
    CONNECTOR_SYNC_STARTED = "connector.sync_started"
    CONNECTOR_SYNC_COMPLETED = "connector.sync_completed"
    CONNECTOR_SYNC_FAILED = "connector.sync_failed"
    INVENTORY_SYNCED = "inventory.synced"
    CATALOG_SYNCED = "catalog.synced"
    CUSTOMERS_SYNCED = "customers.synced"


class EventMetadata(BaseModel):
    """Metadatos comunes a todos los eventos"""
    event_id: UUID = Field(default_factory=uuid4)
    event_type: EventType
    event_version: int = Field(default=1, description="Vital para migraciones sin rotura")
    tenant_id: UUID
    agent_id: UUID | None = None
    conversation_id: UUID | None = None
    customer_id: UUID | None = None
    
    # Event Sourcing Context
    aggregate_type: str = Field(default="system")
    aggregate_id: UUID | None = None
    
    # Operational Intelligence
    severity: str = Field(default="low")         # low, medium, high, critical
    business_impact: str | None = None           # revenue, ops, retention, security
    priority_score: int = Field(default=0)       # 0-100, para sorting/queues/Copilot
    tags: list[str] = Field(default_factory=list)  # ["vip", "payment", "sla-risk"]
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: UUID | None = None  # Para tracing distribuido
    causation_id: UUID | None = None    # Para reconstruir causalidad
    
    model_config = ConfigDict(frozen=True)


class MessageReceivedPayload(BaseModel):
    """Payload para message.received"""
    channel: str  # 'whatsapp', 'telegram', 'webchat'
    from_number: str
    message_id: str
    content: str
    message_type: str = "text"  # text, image, audio, document
    metadata: dict = Field(default_factory=dict)


class LeadQualifiedPayload(BaseModel):
    """Payload para lead.qualified"""
    lead_id: UUID
    score: float = Field(ge=0, le=100)
    intent: str
    sentiment: str  # positive, neutral, negative
    urgency: str = Field(pattern="^(low|medium|high|critical)$")
    recommended_action: str
    context_summary: str | None = None


class HandoffRequestedPayload(BaseModel):
    """Payload para handoff.requested"""
    from_agent: str  # 'ai', 'human'
    to_agent: str
    reason: str
    context_snapshot: dict
    priority: str = Field(pattern="^(low|medium|high)$")


class VoiceTranscriptionChunkPayload(BaseModel):
    """STT parcial en tiempo real"""
    call_id: str
    chunk_text: str
    is_final: bool
    confidence: float = Field(ge=0.0, le=1.0)
    latency_ms: int


class AgentInterruptedPayload(BaseModel):
    """Usuario interrumpe a la IA durante generación de voz"""
    call_id: str
    interruption_point_ms: int
    user_utterance_preview: str
    ai_response_aborted: bool = True

class EmptyPayload(BaseModel):
    """Payload vacío para eventos que no lo requieren"""
    pass

class OrchestratorStartedPayload(BaseModel):
    conversation_id: UUID
    agent_id: UUID
    input_preview: str = Field(..., max_length=200)
    steps_planned: List[str]

class OrchestratorStepCompletedPayload(BaseModel):
    conversation_id: UUID
    step: str  
    duration_ms: int
    success: bool
    metadata: Optional[Dict[str, Any]] = None

class PolicyViolationPayload(BaseModel):
    tenant_id: UUID
    agent_id: UUID
    rule_id: str
    rule_name: str
    attempted_action: str
    context_snapshot: Dict[str, Any]
    severity: str # Literal["low", "medium", "high", "critical"]

class ToolExecutedPayload(BaseModel):
    tool_name: str
    tenant_id: UUID
    execution_id: str
    input_summary: str
    output_summary: str
    duration_ms: int
    success: bool

class ResponseGeneratedPayload(BaseModel):
    conversation_id: UUID
    response_preview: str = Field(..., max_length=200)
    tokens_used: int
    confidence: float
    requires_review: bool

class BillingAlertPayload(BaseModel):
    alert_id: UUID
    tenant_id: UUID
    alert_type: str # BillingAlertType
    resource: str # UsageResource
    current_usage: float
    limit: float
    message: str
    actionable: bool
    created_at: datetime

class PaymentCompletedPayload(BaseModel):
    order_id: str
    amount: float
    method: str
    old_status: str

class PaymentFailedPayload(BaseModel):
    order_id: str
    reason: str

# Union de todos los payloads para tipado seguro
EventPayload = Union[
    MessageReceivedPayload,
    LeadQualifiedPayload,
    HandoffRequestedPayload,
    VoiceTranscriptionChunkPayload,
    AgentInterruptedPayload,
    EmptyPayload,
    OrchestratorStartedPayload,
    OrchestratorStepCompletedPayload,
    PolicyViolationPayload,
    ToolExecutedPayload,
    ResponseGeneratedPayload,
    BillingAlertPayload,
    PaymentCompletedPayload,
    PaymentFailedPayload
]


class DomainEvent(BaseModel):
    """Evento de dominio tipado y serializable"""
    metadata: EventMetadata
    payload: EventPayload
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def to_redis_stream(self) -> dict[str, str]:
        """Convierte el evento al formato para Redis Streams"""
        import json
        from pydantic.json import pydantic_encoder
        
        return {
            "event_type": self.metadata.event_type.value,
            "tenant_id": str(self.metadata.tenant_id),
            "data": json.dumps(self.model_dump(), default=pydantic_encoder),
        }
