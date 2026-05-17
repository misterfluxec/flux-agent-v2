import logging
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from runtime.runtime_metrics import RuntimeMetrics

logger = logging.getLogger(__name__)

class SLOViolation(BaseModel):
    metric: str
    current_value: float
    threshold: float
    message: str

class SLOReport(BaseModel):
    healthy: bool
    violations: List[SLOViolation]

class RuntimeSLO(BaseModel):
    """
    Motor de Service Level Objectives para el Runtime.
    Transforma métricas en alertas accionables.
    """
    max_p95_latency_ms: int = Field(default=5000, description="Latencia de inferencia + tools (P95)")
    max_debate_time_ms: int = Field(default=15000, description="Tiempo máximo en loop CAMEL")
    max_tool_failure_rate: float = Field(default=0.05, description="Tasa máxima tolerada de fallos de tools (5%)")
    max_handoff_rate: float = Field(default=0.15, description="Porcentaje máximo de derivaciones a humanos (15%)")
    min_debate_success_rate: float = Field(default=0.90, description="Tasa mínima de consensos resueltos")
    
    def evaluate(self, metrics: RuntimeMetrics) -> SLOReport:
        """
        Evalúa el status actual de las métricas contra los SLOs definidos.
        """
        violations = []
        
        # Evaluar Tool Failures
        # En una versión real, esto sería una tasa sobre el tiempo. Usamos una aproximación
        if metrics.metrics.get("tool_failures", 0) > 100: # Threshold dummy temporal
            pass 
            
        # Evaluar Human Handoff Rate
        handoff_rate = metrics.metrics.get("human_handoff_rate", 0.0)
        if handoff_rate > self.max_handoff_rate:
            violations.append(SLOViolation(
                metric="human_handoff_rate",
                current_value=handoff_rate,
                threshold=self.max_handoff_rate,
                message=f"Human handoff rate ({handoff_rate:.2%}) excede SLO ({self.max_handoff_rate:.2%})"
            ))
            
        # Evaluar Debate Success
        debate_success = metrics.metrics.get("debate_success_rate", 1.0)
        if debate_success < self.min_debate_success_rate and metrics._counters["total_debates"] > 5:
            violations.append(SLOViolation(
                metric="debate_success_rate",
                current_value=debate_success,
                threshold=self.min_debate_success_rate,
                message=f"Debate success rate ({debate_success:.2%}) bajo SLO ({self.min_debate_success_rate:.2%})"
            ))
            
        return SLOReport(
            healthy=len(violations) == 0,
            violations=violations
        )
