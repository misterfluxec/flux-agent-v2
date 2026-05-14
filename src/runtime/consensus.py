from enum import StrEnum
from pydantic import BaseModel
from typing import List, Optional

class ConsensusStrategy(StrEnum):
    """
    Estrategias para que la capa CAMEL Debate resuelva discusiones entre agentes.
    """
    MAJORITY = "MAJORITY"           # Gana la mayoría (requiere número impar de agentes)
    SUPERMAJORITY = "SUPERMAJORITY" # Requiere 2/3 o más
    WEIGHTED = "WEIGHTED"           # El voto de ciertos roles vale más (ej: Compliance gana sobre Sales en temas de riesgo)
    ESCALATE = "ESCALATE"           # Si no hay acuerdo unánime, escala inmediatamente al humano

class AgentVote(BaseModel):
    agent_id: str
    weight: float = 1.0
    confidence: float
    decision: str
    reason: str

class ConsensusResult(BaseModel):
    decision: str
    votes: List[AgentVote]
    strategy_used: ConsensusStrategy
    escalated: bool = False

class ConsensusEngine:
    @staticmethod
    def resolve(votes: List[AgentVote], strategy: ConsensusStrategy) -> ConsensusResult:
        if not votes:
            return ConsensusResult(decision="NO_VOTES", votes=[], strategy_used=strategy, escalated=True)
            
        if strategy == ConsensusStrategy.WEIGHTED:
            scores = {}
            for v in votes:
                scores[v.decision] = scores.get(v.decision, 0) + (v.weight * v.confidence)
            
            best_decision = max(scores.items(), key=lambda x: x[1])[0]
            return ConsensusResult(decision=best_decision, votes=votes, strategy_used=strategy)
            
        elif strategy == ConsensusStrategy.MAJORITY:
            counts = {}
            for v in votes:
                counts[v.decision] = counts.get(v.decision, 0) + 1
            
            best_decision = max(counts.items(), key=lambda x: x[1])[0]
            # Empate simple en mayoría se escala para ser conservadores
            if list(counts.values()).count(counts[best_decision]) > 1:
                return ConsensusResult(decision="TIE", votes=votes, strategy_used=strategy, escalated=True)
                
            return ConsensusResult(decision=best_decision, votes=votes, strategy_used=strategy)
            
        # Para prototipo, fallback a mayoría o escalar
        return ConsensusResult(decision="UNRESOLVED", votes=votes, strategy_used=strategy, escalated=True)
