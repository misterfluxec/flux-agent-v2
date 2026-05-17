from typing import List, Dict, Any, Callable, Coroutine
import logging
import asyncio

logger = logging.getLogger(__name__)

class SagaStep:
    def __init__(self, name: str, action: Callable[..., Coroutine[Any, Any, Any]], compensation: Callable[..., Coroutine[Any, Any, Any]]):
        self.name = name
        self.action = action
        self.compensation = compensation

class SagaResult:
    def __init__(self, success: bool, results: Dict[str, Any] = None, error: Exception = None):
        self.success = success
        self.results = results or {}
        self.error = error

class SagaManager:
    """
    Saga Coordinator para ejecutar flujos de transacciones distribuidas.
    Asegura que si un paso falla, se llamen a las compensaciones de los pasos
    previamente completados en sort_order inverso.
    """
    def __init__(self, steps: List[SagaStep]):
        self.steps = steps

    async def execute(self, context: Dict[str, Any]) -> SagaResult:
        """
        Ejecuta los pasos de la saga secuencialmente.
        Si hay un fallo, gatilla el proceso de compensación.
        """
        completed_steps = []
        results = {}
        
        logger.info(f"[SagaManager] Comenzando saga de {len(self.steps)} pasos.")
        
        for step in self.steps:
            logger.debug(f"[SagaManager] Ejecutando acción: {step.name}")
            try:
                # El contexto se pasa al step, y el resultado se guarda
                step_result = await step.action(context, results)
                results[step.name] = step_result
                completed_steps.append(step)
            except Exception as e:
                logger.error(f"[SagaManager] Falló la acción: {step.name} - {e}. Iniciando compensación.")
                await self.compensate(completed_steps, context, results)
                return SagaResult(success=False, results=results, error=e)
                
        logger.info("[SagaManager] Saga completada con éxito.")
        return SagaResult(success=True, results=results)

    async def compensate(self, completed_steps: List[SagaStep], context: Dict[str, Any], results: Dict[str, Any]):
        """
        Ejecuta las compensaciones en sort_order inverso.
        """
        # Se invierte la lista para compensar desde el último completado hasta el primero
        for step in reversed(completed_steps):
            logger.warning(f"[SagaManager] Ejecutando compensación: {step.name}")
            try:
                await step.compensation(context, results)
            except Exception as e:
                # Si una compensación falla, debe haber intervención manual o encolamiento en DLQ
                logger.critical(f"[SagaManager] ¡FALLO CRÍTICO EN COMPENSACIÓN!: {step.name} - {e}")
                # Dependiendo del diseño, podríamos no detener el bucle para intentar compensar el resto
