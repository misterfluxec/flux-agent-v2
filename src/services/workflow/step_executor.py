from typing import Dict, Any, Optional
from dataclasses import dataclass

from domain.workflow_schemas import NodeDefinition, WorkflowActionType, StepRunStatus
from services.workflow.json_logic_evaluator import JsonLogicEvaluator

@dataclass
class StepExecutionResult:
    status: StepRunStatus
    output: Dict[str, Any]
    next_node_id: Optional[str] = None
    error_message: Optional[str] = None

class BaseStepExecutor:
    async def execute(self, node: NodeDefinition, context: Dict[str, Any]) -> StepExecutionResult:
        raise NotImplementedError()

class ConditionStepExecutor(BaseStepExecutor):
    async def execute(self, node: NodeDefinition, context: Dict[str, Any]) -> StepExecutionResult:
        rule = node.condition_rules
        if not rule:
            return StepExecutionResult(StepRunStatus.FAILED, {}, error_message="No condition rules defined")
            
        try:
            is_true = JsonLogicEvaluator.evaluate(rule, context)
            next_node = node.on_true_node_id if is_true else node.on_false_node_id
            
            return StepExecutionResult(
                status=StepRunStatus.COMPLETED,
                output={"result": is_true},
                next_node_id=next_node
            )
        except Exception as e:
            return StepExecutionResult(StepRunStatus.FAILED, {}, error_message=str(e))

class HumanTaskStepExecutor(BaseStepExecutor):
    async def execute(self, node: NodeDefinition, context: Dict[str, Any]) -> StepExecutionResult:
        # 1. Create HumanTask in DB
        # 2. Return SUSPENDED so the engine pauses execution
        return StepExecutionResult(
            status=StepRunStatus.SUSPENDED,
            output={"human_task_created": True, "task_id": "uuid"},
            next_node_id=node.next_node_id
        )

class StepExecutorFactory:
    def __init__(self):
        self.executors = {
            WorkflowActionType.CONDITION: ConditionStepExecutor(),
            WorkflowActionType.HUMAN_TASK: HumanTaskStepExecutor(),
            # Register others like AITaskStepExecutor, etc.
        }
        
    def get_executor(self, action_type: WorkflowActionType) -> BaseStepExecutor:
        executor = self.executors.get(action_type)
        if not executor:
            raise ValueError(f"No executor found for action type {action_type}")
        return executor
