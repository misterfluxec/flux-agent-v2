# =============================================================================
# FLUXAGENT V2 — TASK TRACER (PASOS Y MÉTRICAS)
# =============================================================================
# Mide la duración de los pasos y emite telemetría técnica.
# =============================================================================

import time
import logging
from typing import Optional, Dict, Any
from .logger import get_logger

logger = get_logger("telemetry.tracer")

class TaskTracer:
    """
    Rastreador de ejecución que mide latencias por paso.
    """
    def __init__(self, task_id: str):
        self.task_id = task_id
        self.start_times: Dict[str, float] = {}

    def start_span(self, name: str):
        """Inicia la medición de un paso."""
        self.start_times[name] = time.perf_counter()
        logger.info(f"Span iniciado: {name}", step=name, action="start")

    def end_span(self, name: str, status: str = "success", **metrics):
        """Finaliza la medición y emite telemetría."""
        start_time = self.start_times.pop(name, None)
        if start_time:
            duration = (time.perf_counter() - start_time) * 1000 # ms
            
            # Alerta automática si el paso es lento (> 10 segundos)
            log_level = "info"
            if duration > 10000:
                log_level = "warning"
            
            getattr(logger, log_level)(
                f"Span finalizado: {name} ({status})", 
                step=name, 
                duration_ms=round(duration, 2),
                status=status,
                **metrics
            )
            return duration
        return 0.0
