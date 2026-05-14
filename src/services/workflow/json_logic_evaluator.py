import logging
from typing import Dict, Any
from json_logic import jsonLogic

logger = logging.getLogger(__name__)

class WorkflowEvaluationError(Exception):
    pass

class JsonLogicEvaluator:
    """
    Sandboxed execution engine for Workflow conditions.
    Uses JsonLogic to evaluate complex business rules safely without arbitrary code execution.
    """
    
    @staticmethod
    def evaluate(rule: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """
        Evaluates a JsonLogic rule against the provided context data.
        Returns a boolean indicating if the condition passed.
        """
        try:
            result = jsonLogic(rule, data)
            if not isinstance(result, bool):
                logger.warning(f"[JsonLogic] Rule evaluated to non-boolean: {result}. Coercing to bool.")
                return bool(result)
            return result
        except Exception as e:
            logger.error(f"[JsonLogic] Error evaluating rule: {e}")
            raise WorkflowEvaluationError(f"Failed to evaluate rule: {str(e)}")
