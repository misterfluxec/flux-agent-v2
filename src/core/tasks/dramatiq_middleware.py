import dramatiq
import logging
from .context import TaskContext, task_context

logger = logging.getLogger(__name__)

class TenantContextMiddleware(dramatiq.Middleware):
    """
    Middleware de Dramatiq para propagar el ContextVar de tenant_id.
    Permite que los workers de dramatiq tengan acceso al contexto aislando el tenant_id.
    """
    
    def before_enqueue(self, broker, message, delay):
        # Cuando se encola una tarea, inyectar el contexto actual en options
        ctx = task_context.get()
        if ctx:
            message.options["task_context"] = {
                "task_id": ctx.task_id,
                "tenant_id": ctx.tenant_id,
                "correlation_id": ctx.correlation_id
            }

    def before_process_message(self, broker, message):
        # Antes de procesar, restaurar el ContextVar en el worker
        ctx_data = message.options.get("task_context")
        if ctx_data:
            ctx = TaskContext(**ctx_data)
            # Guardamos el token en las opciones para usarlo en after_process_message
            token = task_context.set(ctx)
            message.options["_task_context_token"] = token
            logger.debug(f"[TenantContextMiddleware] ContextVar restaurado para tenant_id: {ctx.tenant_id}")

    def after_process_message(self, broker, message, *, result=None, exception=None):
        # Limpiar el contextvar para evitar side-effects en el worker
        token = message.options.get("_task_context_token")
        if token:
            task_context.reset(token)
