import time
import traceback
import logging
from contextlib import asynccontextmanager
from typing import Optional

from .context import TaskContext, task_context
from .emitter import ProgressEmitter

logger = logging.getLogger(__name__)

class TaskStep:
    def __init__(self, runner: "AsyncTaskRunner", label: str, weight: float):
        self.runner = runner
        self.label = label
        self.weight = weight
        self.start_time = 0

    async def __aenter__(self):
        self.start_time = time.time()
        # Emitimos un evento al inicio del paso
        await ProgressEmitter.emit("task_step_started", {
            "task_id": self.runner.id,
            "tenant_id": self.runner.tenant_id,
            "label": self.label,
            "weight": self.weight
        })
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_val:
            await ProgressEmitter.emit("task_step_failed", {
                "task_id": self.runner.id,
                "tenant_id": self.runner.tenant_id,
                "label": self.label,
                "error": str(exc_val),
                "duration_ms": duration_ms
            })
            # No suprimimos la excepción en el paso, se propaga al runner
            return False
            
        await ProgressEmitter.emit("task_step_completed", {
            "task_id": self.runner.id,
            "tenant_id": self.runner.tenant_id,
            "label": self.label,
            "duration_ms": duration_ms
        })
        return False


class AsyncTaskRunner:
    """
    Runner para tareas asíncronas con soporte para ContextVars y progreso.
    Crea un contexto seguro para aislar el tenant_id.
    """
    def __init__(self, task_id: str, tenant_id: str, correlation_id: Optional[str] = None):
        self.id = task_id
        self.tenant_id = tenant_id
        self.correlation_id = correlation_id
        self._token = None
        self.start_time = 0

    async def __aenter__(self):
        self.start_time = time.time()
        
        # Establecer ContextVar
        ctx = TaskContext(
            task_id=self.id, 
            tenant_id=self.tenant_id, 
            correlation_id=self.correlation_id
        )
        self._token = task_context.set(ctx)
        
        await ProgressEmitter.emit("task_started", {
            "task_id": self.id,
            "tenant_id": self.tenant_id,
            "correlation_id": self.correlation_id
        })
        return self

    def step(self, label: str, weight: float = 1.0):
        return TaskStep(self, label, weight)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        duration_ms = int((time.time() - self.start_time) * 1000)
        
        if exc_val:
            logger.error(f"[AsyncTaskRunner] Error en tarea {self.id}: {exc_val}")
            await ProgressEmitter.emit("task_failed", {
                "task_id": self.id,
                "tenant_id": self.tenant_id,
                "error": str(exc_val),
                "trace": traceback.format_exc(),
                "duration_ms": duration_ms
            })
        else:
            await ProgressEmitter.emit("task_completed", {
                "task_id": self.id,
                "tenant_id": self.tenant_id,
                "duration_ms": duration_ms
            })
            
        # Restaurar ContextVar a su status anterior
        if self._token:
            task_context.reset(self._token)
            
        return False  # Propagar excepción si existe
