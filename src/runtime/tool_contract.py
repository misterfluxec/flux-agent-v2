from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import StrEnum

class RiskLevel(StrEnum):
    INFO = "INFO"           # Operaciones de lectura (ej: check_stock)
    MODERATE = "MODERATE"   # Operaciones reversibles (ej: draft_order)
    CRITICAL = "CRITICAL"   # Operaciones irreversibles o de dinero (ej: refund, process_payment)

class ToolContract(BaseModel):
    """
    Define la gobernanza estricta para una herramienta.
    Ninguna herramienta puede ser ejecutada sin adherirse a este contrato.
    """
    id: str = Field(..., description="ID de la herramienta (ej: process_refund)")
    risk_level: RiskLevel = Field(..., description="Nivel de riesgo de la operación")
    idempotent: bool = Field(..., description="¿Es segura para reintentar?")
    timeout_ms: int = Field(default=5000, description="Tiempo máximo de ejecución")
    requires_human: bool = Field(default=False, description="¿Requiere aprobación humana (Human-in-the-loop)?")
    max_calls_per_session: int = Field(default=10, description="Límite por sesión/conversación para evitar loops")
    side_effects: bool = Field(default=False, description="¿Muta status en sistemas externos?")
    allowed_roles: List[str] = Field(default_factory=list, description="Roles permitidos para usarla (vacío = cualquiera)")
    
    # Restricciones de valor (opcionales, ej: no hacer un refund > 100 USD)
    max_amount_allowed: Optional[float] = None
