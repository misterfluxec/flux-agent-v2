from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID

class ConversationState(StrEnum):
    IDLE = "idle"
    AI_THINKING = "ai_thinking"
    AI_RESPONDING = "ai_responding"
    HUMAN_TAKEOVER = "human_takeover"
    AI_OBSERVING = "ai_observing"
    CLOSED = "closed"

VALID_TRANSITIONS = {
    ConversationState.IDLE: [ConversationState.AI_THINKING, ConversationState.CLOSED],
    ConversationState.AI_THINKING: [ConversationState.AI_RESPONDING, ConversationState.HUMAN_TAKEOVER],
    ConversationState.AI_RESPONDING: [ConversationState.HUMAN_TAKEOVER, ConversationState.AI_OBSERVING, ConversationState.IDLE],
    ConversationState.HUMAN_TAKEOVER: [ConversationState.AI_OBSERVING, ConversationState.AI_THINKING, ConversationState.CLOSED],
    ConversationState.AI_OBSERVING: [ConversationState.AI_THINKING, ConversationState.HUMAN_TAKEOVER, ConversationState.CLOSED],
    ConversationState.CLOSED: []
}

class ConversationContext(BaseModel):
    conversation_id: UUID
    tenant_id: UUID
    agent_id: UUID
    current_state: ConversationState = ConversationState.IDLE
    owner_id: str | None = None  # "ai" o UUID del usuario humano
    lock_expires_at: datetime | None = None
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

class StateTransitionEvent(BaseModel):
    conversation_id: UUID
    from_state: ConversationState
    to_state: ConversationState
    triggered_by: str  # "ai", "human", "system", "timeout"
    reason: str | None = None
    metadata: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
