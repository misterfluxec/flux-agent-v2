from contextvars import ContextVar
from dataclasses import dataclass
from typing import Optional

@dataclass
class TaskContext:
    task_id: str
    tenant_id: str
    correlation_id: Optional[str] = None

# Variable de contexto global para la tarea actual
task_context: ContextVar[Optional[TaskContext]] = ContextVar("task_context", default=None)

def get_current_task_id() -> Optional[str]:
    ctx = task_context.get()
    return ctx.task_id if ctx else None

def get_current_tenant_id() -> Optional[str]:
    ctx = task_context.get()
    return ctx.tenant_id if ctx else None
