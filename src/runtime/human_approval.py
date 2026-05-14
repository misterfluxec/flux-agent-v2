from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from typing import Optional
from enum import StrEnum

class ApprovalDecision(StrEnum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"

class ApprovalRequest(BaseModel):
    """
    Solicitud formal de Human-In-The-Loop para acciones críticas.
    """
    id: str = Field(..., description="ID único de la solicitud de aprobación")
    action: str = Field(..., description="Acción o herramienta que requiere aprobación")
    reason: str = Field(..., description="Razón por la cual se pide aprobación")
    confidence: float = Field(..., description="Confianza del Agente en proponer esta acción")
    requester: str = Field(..., description="Entidad o agente que solicita la aprobación")
    approver_role: str = Field(..., description="Rol humano requerido para aprobar (ej: 'manager', 'finance')")
    expires_at: datetime = Field(..., description="Fecha de expiración de la solicitud")
    context_snapshot: dict = Field(default_factory=dict, description="Contexto completo de por qué se pide la aprobación")
    correlation_id: str = Field(..., description="ID de correlación para reanudar el flujo en el graph runtime")
    
    @classmethod
    def create(cls, action: str, reason: str, confidence: float, requester: str, approver_role: str, correlation_id: str, timeout_mins: int = 60, context: dict = None):
        import uuid
        return cls(
            id=f"apr_{uuid.uuid4()}",
            action=action,
            reason=reason,
            confidence=confidence,
            requester=requester,
            approver_role=approver_role,
            expires_at=datetime.utcnow() + timedelta(minutes=timeout_mins),
            context_snapshot=context or {},
            correlation_id=correlation_id
        )

class ApprovalResponse(BaseModel):
    request_id: str
    decision: ApprovalDecision
    decided_by: str
    decision_reason: Optional[str] = None
    decided_at: datetime = Field(default_factory=datetime.utcnow)
