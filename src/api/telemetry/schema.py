from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field

# =============================================================================
# SCHEMAS DE EVENTOS (INTERNOS Y EXTERNOS)
# =============================================================================

class AuditEntry(BaseModel):
    """Entrada de auditoría traducida a lenguaje de negocio (human-readable)"""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    level: Literal["info", "warning", "error", "success"] = "info"
    message: str # Ej: "Se indexaron 142 fragmentos de conocimiento"
    details: Optional[Dict[str, Any]] = None

class StepPayload(BaseModel):
    """Estado individual de un paso dentro de una tarea"""
    label: str
    weight: float = 1.0
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None

class TaskTelemetryResponse(BaseModel):
    """Representación completa del status de una tarea para el Frontend"""
    task_id: str
    tenant_id: str
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    progress: float = Field(0.0, ge=0.0, le=100.0) # Progreso global de 0 a 100
    current_step: Optional[str] = None
    steps: List[StepPayload] = Field(default_factory=list)
    logs: List[AuditEntry] = Field(default_factory=list)
    started_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

class ProgressEvent(BaseModel):
    """Evento atómico enviado por WS para actualización delta"""
    event_type: Literal["task_started", "step_started", "step_completed", "step_failed", "task_completed", "task_failed"]
    task_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    data: Dict[str, Any]
