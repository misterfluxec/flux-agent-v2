from enum import StrEnum
from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import datetime
from uuid import UUID, uuid4
from typing import Literal, Dict, Optional, Any
import math

class UsageResource(StrEnum):
    """Recursos medibles para billing"""
    LLM_TOKENS_INPUT = "llm:tokens:input"
    LLM_TOKENS_OUTPUT = "llm:tokens:output"
    LLM_REQUESTS = "llm:requests"
    EMBEDDINGS_GENERATED = "embeddings:generated"
    RAG_QUERIES = "rag:queries"
    VECTOR_STORE_READS = "vector:reads"
    STT_SECONDS = "stt:seconds"
    TTS_SECONDS = "tts:seconds"
    VOICE_CALL_MINUTES = "voice:call_minutes"
    TOOL_EXECUTIONS = "tool:executions"
    TOOL_EXECUTIONS_PREMIUM = "tool:executions:premium"
    WEBSOCKET_MINUTES = "websocket:minutes"
    EVENT_BUS_MESSAGES = "eventbus:messages"
    STORAGE_MB = "storage:megabytes"
    MEMORY_EPISODIC_ENTRIES = "memory:episodic:entries"

class UsageTier(StrEnum):
    """Niveles de pricing por recurso"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class UsageRecord(BaseModel):
    """Registro atómico de consumo"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    agent_id: Optional[UUID] = None
    resource: UsageResource
    amount: float = Field(..., ge=0)
    unit: str = Field(..., description="Ej: 'tokens', 'seconds', 'requests'")
    cost_usd: float = Field(default=0.0, ge=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    correlation_id: Optional[UUID] = None
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
    
    @model_validator(mode='after')
    def validate_amount_precision(self) -> 'UsageRecord':
        if self.resource in [UsageResource.LLM_TOKENS_INPUT, UsageResource.LLM_TOKENS_OUTPUT]:
            self.amount = math.floor(self.amount)
        return self

class QuotaDefinition(BaseModel):
    """Definición de límite por recurso y plan"""
    resource: UsageResource
    plan: UsageTier
    limit: float  # -1 = ilimitado
    period: str # Literal["hour", "day", "month"] = "month"
    overage_allowed: bool = False
    overage_rate: Optional[float] = None
    
    def is_exceeded(self, consumed: float) -> bool:
        if self.limit < 0:
            return False
        return consumed >= self.limit
    
    def remaining(self, consumed: float) -> float:
        if self.limit < 0:
            return float('inf')
        return max(0, self.limit - consumed)

class QuotaCheckRequest(BaseModel):
    """Request para verificar disponibilidad antes de consumir"""
    tenant_id: UUID
    resource: UsageResource
    requested_amount: float
    dry_run: bool = False

class QuotaCheckResponse(BaseModel):
    """Respuesta de verificación de quota"""
    allowed: bool
    reason: Optional[str] = None
    remaining: float
    reset_at: datetime
    overage_cost_usd: Optional[float] = None
    suggested_action: Optional[str] = None

class BillingAlertType(StrEnum):
    THRESHOLD_80 = "threshold_80"
    THRESHOLD_100 = "threshold_100"
    OVERAGE_CHARGED = "overage_charged"
    PLAN_DOWNGRADE_WARNING = "plan_downgrade_warning"

class BillingAlert(BaseModel):
    """Alerta para notificar al tenant"""
    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    alert_type: BillingAlertType
    resource: UsageResource
    current_usage: float
    limit: float
    message: str
    actionable: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})
