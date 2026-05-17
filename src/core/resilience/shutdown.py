import logging
import asyncio
from typing import Callable, List

logger = logging.getLogger(__name__)

class WorkerLifecycleHooks:
    """
    Gestiona el graceful shutdown de workers y componentes asíncronos.
    Asegura que los procesos vacíen (drain) la cola o cancelen
    limpiamente antes de que el contenedor muera por SIGTERM.
    """
    _shutdown_hooks: List[Callable] = []

    @classmethod
    def register_hook(cls, hook: Callable):
        cls._shutdown_hooks.append(hook)

    @classmethod
    async def execute_drain(cls, timeout: int = 15):
        """
        Ejecuta todos los hooks registrados con un timeout.
        """
        logger.info(f"🛑 Iniciando Graceful Drain (timeout {timeout}s)...")
        tasks = []
        for hook in cls._shutdown_hooks:
            import inspect
            if inspect.iscoroutinefunction(hook):
                tasks.append(hook())
            else:
                hook()
                
        if tasks:
            try:
                await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout)
                logger.info("✅ Graceful Drain completado.")
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout durante el Graceful Drain. Forzando salida.")
            except Exception as e:
                logger.error(f"❌ Error durante el drain: {e}")
