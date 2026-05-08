from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from uuid import UUID, uuid4
from typing import Literal, Dict, List, Optional, Any

class OrchestratorStep(StrEnum):
    MEMORY_RETRIEVAL = "memory.retrieval"
    INTENT_DETECTION = "intent.detection"
    POLICY_EVALUATION = "policy.evaluation"
    TOOL_SELECTION = "tool.selection"
    TOOL_EXECUTION = "tool.execution"
    RESPONSE_GENERATION = "response.generation"
    MEMORY_PERSISTENCE = "memory.persistence"
    EVENT_EMISSION = "event.emission"

class OrchestratorContext(BaseModel):
    """Contexto completo que viaja por el pipeline del orchestrator"""
    conversation_id: UUID
    tenant_id: UUID
    agent_id: UUID
    customer_id: Optional[UUID] = None
    channel: str # "whatsapp", "telegram", "webchat", "voice"
    raw_input: str
    input_metadata: Dict[str, Any] = Field(default_factory=dict)
    correlation_id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Resultados parciales (se van llenando en cada step)
    retrieved_memory: Optional[Dict[str, Any]] = None
    detected_intent: Optional[str] = None
    intent_confidence: Optional[float] = None
    selected_tools: List[str] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    generated_response: Optional[str] = None
    policy_decisions: List[Any] = Field(default_factory=list) # List[PolicyEvaluationResult]
    completed_steps: List[OrchestratorStep] = Field(default_factory=list)
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def metadata_for_event(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "agent_id": self.agent_id,
            "conversation_id": self.conversation_id,
            "customer_id": self.customer_id,
            "correlation_id": self.correlation_id,
        }

class ProcessMessageInput(BaseModel):
    """Input público del orchestrator (desde routers o event bus)"""
    conversation_id: UUID
    tenant_id: UUID
    agent_id: UUID
    customer_id: Optional[UUID] = None
    channel: str
    message: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Opcional: forzar modo (útil para testing)
    force_tool: Optional[str] = None
    skip_policy: bool = Field(default=False, description="Solo para testing interno")

class ToolSelectionResult(BaseModel):
    """Resultado de la fase de selección de herramientas"""
    selected_tools: List[str]
    reasoning: str
    confidence: float = Field(ge=0.0, le=1.0)
    fallback_to_text: bool = False

class ResponseGenerationResult(BaseModel):
    """Resultado de la generación de respuesta"""
    text: str
    confidence: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool = False
    suggested_followup: Optional[str] = None
    tone_applied: str
    tokens_used: int

class OrchestratorOutput(BaseModel):
    """Output final del orchestrator"""
    success: bool
    response: Optional[str] = None
    executed_tools: List[Dict[str, Any]] = Field(default_factory=list)
    memory_updated: bool = False
    events_emitted: List[str] = Field(default_factory=list)  # IDs de eventos publicados
    error: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    processing_time_ms: int
    steps_completed: List[OrchestratorStep] = Field(default_factory=list)
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    def to_event_payload(self):
        from src.domain.events import ResponseGeneratedPayload
        return ResponseGeneratedPayload(
            conversation_id=uuid4(), # This should be matched with the original conversation_id in the orchestrator flow
            response_preview=(self.response[:197] + "...") if self.response and len(self.response) > 200 else (self.response or ""),
            tokens_used=0, # Could be calculated
            confidence=1.0,
            requires_review=False
        )
