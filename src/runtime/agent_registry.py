from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import logging

logger = logging.getLogger(__name__)

class AgentCapability(BaseModel):
    agent_id: str
    name: str
    skills: List[str] = Field(default_factory=list)
    cost_per_turn: float = 0.0
    avg_latency_ms: int = 1000
    priority: int = 1
    system_prompt: str
    
class AgentRegistry:
    """
    Registry for dynamic agent selection based on required capabilities and constraints.
    Replaces static routing by hardcoded types.
    """
    
    def __init__(self):
        # In memory registry, to be backed by DB/Redis
        self._agents: Dict[str, AgentCapability] = {}

    def register(self, capability: AgentCapability):
        """Register a new agent capability profile."""
        self._agents[capability.agent_id] = capability
        logger.debug(f"[AgentRegistry] Registered agent: {capability.name} ({capability.agent_id})")

    def get_agent(self, agent_id: str) -> Optional[AgentCapability]:
        return self._agents.get(agent_id)

    def select_best(self, required_skills: List[str] = None, max_latency_ms: int = None, max_cost: float = None) -> Optional[AgentCapability]:
        """
        Selecciona el mejor agente disponible que cumpla los criterios.
        Prioriza: Matches de Skills -> Menor latencia -> Menor costo.
        """
        candidates = list(self._agents.values())
        
        if required_skills:
            req_set = set(required_skills)
            candidates = [a for a in candidates if req_set.issubset(set(a.skills))]
            
        if max_latency_ms:
            candidates = [a for a in candidates if a.avg_latency_ms <= max_latency_ms]
            
        if max_cost:
            candidates = [a for a in candidates if a.cost_per_turn <= max_cost]
            
        if not candidates:
            return None
            
        # Ordenamos por prioridad (mayor primero), luego latencia, luego costo
        candidates.sort(key=lambda a: (-a.priority, a.avg_latency_ms, a.cost_per_turn))
        
        best = candidates[0]
        logger.info(f"[AgentRegistry] Selected {best.name} for requested constraints.")
        return best
