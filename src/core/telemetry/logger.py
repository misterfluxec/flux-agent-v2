# =============================================================================
# FLUXAGENT V2 — LOGGER ESTRUCTURADO UNIFICADO
# =============================================================================
# Emite JSON validado enriquecido con el contexto completo de ejecución.
# =============================================================================

import json
import logging
import traceback
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from core.tasks.context import get_current_task_id, get_current_tenant_id
from .context import get_correlation_id, get_causation_id

class LogSchema(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    level: str
    module: str
    message: str
    correlation_id: str
    causation_id: Optional[str] = None
    tenant_id: Optional[str] = None
    task_id: Optional[str] = None
    duration_ms: Optional[float] = None
    error: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = {}

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.module = name

    def _log(self, level: str, msg: str, duration: Optional[float] = None, error: Optional[Exception] = None, **extra):
        # Capturar info de error si existe
        error_data = None
        if error:
            error_data = {
                "type": type(error).__name__,
                "message": str(error),
                "stack": traceback.format_exc() if level in ["ERROR", "CRITICAL"] else None
            }

        log_entry = LogSchema(
            level=level,
            module=self.module,
            message=msg,
            correlation_id=get_correlation_id(),
            causation_id=get_causation_id(),
            tenant_id=str(get_current_tenant_id()) if get_current_tenant_id() else None,
            task_id=get_current_task_id(),
            duration_ms=duration,
            error=error_data,
            extra=extra
        )
        
        # Loguear como JSON string
        self.logger.log(
            getattr(logging, level.upper()), 
            log_entry.model_dump_json(exclude_none=True)
        )

    def info(self, msg: str, **extra): self._log("INFO", msg, **extra)
    def error(self, msg: str, error: Optional[Exception] = None, **extra): self._log("ERROR", msg, error=error, **extra)
    def warning(self, msg: str, **extra): self._log("WARNING", msg, **extra)
    def debug(self, msg: str, **extra): self._log("DEBUG", msg, **extra)
    def critical(self, msg: str, error: Optional[Exception] = None, **extra): self._log("CRITICAL", msg, error=error, **extra)

def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
