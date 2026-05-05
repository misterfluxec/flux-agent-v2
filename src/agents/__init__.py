# =============================================================================
# FLUXAGENT V2 — MÓDULO DE AGENTES IA
# =============================================================================
# Este paquete contiene toda la lógica de los agentes de inteligencia artificial.
#
# Estructura:
#   __init__.py      — Exportaciones públicas del módulo
#   base_agent.py    — Clase base con la interfaz común de todos los agentes
#   sales_agent.py   — Agente de ventas con grafo LangGraph
#   router.py        — Endpoints FastAPI del módulo (crear cuando se necesite)
# =============================================================================

from agents.base_agent import AgenteBase
from agents.sales_agent import AgentDeVentas

__all__ = ["AgenteBase", "AgentDeVentas"]
