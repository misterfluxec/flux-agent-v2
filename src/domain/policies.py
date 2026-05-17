from enum import StrEnum
from pydantic import BaseModel, Field, model_validator, ConfigDict
from datetime import datetime
from uuid import UUID
from typing import Literal, Dict, List, Optional, Any


class PolicyOperator(StrEnum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    MATCHES_REGEX = "matches_regex"


class PolicyCondition(BaseModel):
    """Condición atómica para una regla de política"""
    field: str  # Ej: "tool_name", "tenant_plan", "hour", "discount_amount"
    operator: PolicyOperator
    value: Any
    
    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa la condición contra un contexto"""
        actual = context.get(self.field)
        
        if self.operator == PolicyOperator.EQ:
            return actual == self.value
        elif self.operator == PolicyOperator.NEQ:
            return actual != self.value
        elif self.operator == PolicyOperator.GT:
            return actual > self.value if actual is not None else False
        elif self.operator == PolicyOperator.IN:
            return actual in self.value if isinstance(self.value, list) else False
        elif self.operator == PolicyOperator.MATCHES_REGEX:
            import re
            return bool(re.match(self.value, str(actual))) if actual else False
        
        return False


class PolicyAction(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_APPROVAL = "require_approval"
    MODIFY = "modify"  # Ej: reducir descuento automáticamente
    LOG_ONLY = "log_only"  # Solo auditar, no bloquear


class PolicyRule(BaseModel):
    """Regla de política empresarial"""
    id: str = Field(..., pattern=r"^[a-zA-Z0-9_\-\.]+$")  # Ej: "no_high_discount_basic"
    name: str
    description: Optional[str] = None
    
    # Condiciones (AND lógico entre ellas)
    conditions: List[PolicyCondition] = Field(default_factory=list)
    
    # Acción a tomar si se cumplen las condiciones
    action: PolicyAction
    
    # Metadatos de aplicación
    priority: int = Field(default=100, ge=1, le=1000)  # Mayor = más priority
    enabled: bool = True
    tenant_plans: List[str] = Field(default=["basic", "pro", "enterprise"])
    industries: Optional[List[str]] = None  # Si None, aplica a todas
    tools: Optional[List[str]] = None  # Si None, aplica a todas las herramientas
    
    # Modificación si action == MODIFY
    modifications: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(frozen=True)
    
    @model_validator(mode='after')
    def validate_modifications(self) -> 'PolicyRule':
        if self.action == PolicyAction.MODIFY and not self.modifications:
            raise ValueError("PolicyRule with action=MODIFY must have modifications defined")
        return self


class PolicyEvaluationRequest(BaseModel):
    """Request para evaluar una política"""
    tenant_id: UUID
    agent_id: UUID
    tool_name: str
    input_payload: Dict[str, Any]
    context: Dict[str, Any] = Field(default_factory=dict)  # hour, customer_tier, etc.
    dry_run: bool = False


class PolicyEvaluationResult(BaseModel):
    """Resultado de evaluar una política"""
    rule_id: str
    rule_name: str
    matched: bool  # Si las condiciones se cumplieron
    action: PolicyAction
    decision: str # "allowed", "denied", "requires_approval", "modified"
    reason: Optional[str] = None
    modifications_applied: Optional[Dict[str, Any]] = None
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = ConfigDict(json_encoders={datetime: lambda v: v.isoformat()})


class PolicyEngineOutput(BaseModel):
    """Output completo del Policy Engine"""
    allowed: bool
    requires_approval: bool
    evaluations: List[PolicyEvaluationResult] = Field(default_factory=list)
    final_decision: str  # "allowed", "denied", "modified", "pending_approval"
    applied_modifications: Dict[str, Any] = Field(default_factory=dict)
    audit_log_entry_id: Optional[str] = None
