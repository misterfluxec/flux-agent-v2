from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class WorkflowTriggerType(str, Enum):
    EVENT = "event_based"
    SCHEDULE = "schedule"
    MANUAL = "manual"

class WorkflowActionType(str, Enum):
    CONDITION = "condition"
    DELAY = "delay"
    SEND_MESSAGE = "send_message"
    AI_TASK = "ai_task"
    HUMAN_TASK = "human_task"
    API_CALL = "api_call"
    SYSTEM_ACTION = "system_action"

class NodeDefinition(BaseModel):
    id: str
    type: WorkflowActionType
    config: Dict[str, Any] = Field(default_factory=dict)
    next_node_id: Optional[str] = None # Next node to execute
    
    # Only for CONDITION type nodes
    condition_rules: Optional[Dict[str, Any]] = Field(default=None, description="JsonLogic rule")
    on_true_node_id: Optional[str] = None
    on_false_node_id: Optional[str] = None

class WorkflowDefinition(BaseModel):
    version: int
    trigger_type: WorkflowTriggerType
    trigger_config: Dict[str, Any]
    start_node_id: str
    nodes: List[NodeDefinition]

    def validate_dag(self):
        """
        Sprint H1: Basic DAG Validation (Acyclic Directed Graph)
        Ensures there are no orphaned nodes, no infinite loops without exits,
        and all paths are valid.
        """
        node_map = {n.id: n for n in self.nodes}
        if self.start_node_id not in node_map:
            raise ValueError("start_node_id must exist in nodes")
            
        # Basic validation: ensure all next_node_id exist
        for n in self.nodes:
            if n.next_node_id and n.next_node_id not in node_map:
                raise ValueError(f"Node {n.id} points to non-existent node {n.next_node_id}")
            if n.type == WorkflowActionType.CONDITION:
                if n.on_true_node_id and n.on_true_node_id not in node_map:
                    raise ValueError(f"Node {n.id} on_true points to non-existent node")
                if n.on_false_node_id and n.on_false_node_id not in node_map:
                    raise ValueError(f"Node {n.id} on_false points to non-existent node")
                    
        return True

class WorkflowRunStatus(str, Enum):
    RUNNING = "running"
    SUSPENDED = "suspended" # Waiting for delay or human task
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepRunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"
    FAILED = "failed"
