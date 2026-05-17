import logging
import dramatiq
from dramatiq.middleware import SkipMessage
from core.tasks.context import task_context, TaskContext
from core.tasks.emitter import ProgressEmitter

logger = logging.getLogger(__name__)

class ContextPreservationMiddleware(dramatiq.Middleware):
    """
    Restaura el TaskContext dentro del worker y emite telemetría de reintentos.
    """
    def before_process_message(self, broker, message):
        ctx_data = message.options.get("task_context")
        if ctx_data:
            token = task_context.set(TaskContext(**ctx_data))
            message.options["_task_context_token"] = token

    async def after_process_message(self, broker, message, *, result=None, exception=None):
        ctx = task_context.get()
        token = message.options.get("_task_context_token")
        
        if exception and ctx:
            # Emitimos evento de telemetría indicando el reintento
            try:
                import asyncio
                if asyncio.get_event_loop().is_running():
                    await ProgressEmitter.emit("task_retrying", {
                        "task_id": ctx.task_id,
                        "tenant_id": ctx.tenant_id,
                        "error": str(exception),
                        "retries": message.options.get("retries", 0)
                    })
            except Exception as e:
                logger.debug(f"No se pudo emitir task_retrying: {e}")

        if token:
            task_context.reset(token)

class DLQRoutingMiddleware(dramatiq.Middleware):
    """
    Enruta tareas permanentemente fallidas (max retries alcanzados) a la DLQ.
    """
    def after_process_message(self, broker, message, *, result=None, exception=None):
        if exception:
            retries = message.options.get("retries", 0)
            max_retries = message.options.get("max_retries", 3)
            
            if retries >= max_retries:
                logger.error(f"🚨 DLQ ROUTING: Tarea {message.message_id} falló {retries} veces. Movida a DLQ.")
                # Enviar a cola 'dlq_tasks'
                broker.enqueue(message, queue_name="dlq_tasks")
