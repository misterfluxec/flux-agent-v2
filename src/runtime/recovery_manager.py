from enum import StrEnum
from pydantic import BaseModel
from typing import Dict, Any

class RecoveryAction(StrEnum):
    RETRY = "RETRY"           # Reintentar en la misma capa (ej. timeout de red)
    RESUME = "RESUME"         # Reanudar desde el último checkpoint
    REPLAY = "REPLAY"         # Reconstruir el estado desde el log de eventos
    HANDOFF = "HANDOFF"       # Derivar a operador humano
    CANCEL = "CANCEL"         # Abortar el flujo permanentemente

class FailureContext(BaseModel):
    error_type: str
    message: str
    attempt_count: int
    is_transient: bool
    requires_human_judgment: bool

class RecoveryManager:
    """
    Centraliza las decisiones de recuperación del runtime en lugar de tenerlas
    dispersas entre orchestrator, tool_runtime y handlers individuales.
    """
    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries

    def decide(self, failure: FailureContext) -> RecoveryAction:
        if failure.requires_human_judgment:
            return RecoveryAction.HANDOFF
            
        if failure.is_transient and failure.attempt_count <= self.max_retries:
            return RecoveryAction.RETRY
            
        # Si no es transitorio o superó reintentos, evaluamos si es catastrófico
        if "policy_denied" in failure.error_type.lower():
            return RecoveryAction.CANCEL
            
        # Fallback predeterminado para errores no clasificados persistentes
        return RecoveryAction.HANDOFF
