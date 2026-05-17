# =============================================================================
# FLUXAGENT V2 — DEPENDENCIAS DE INYECCIÓN (AGENT CORE)
# =============================================================================

import os
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database import obtener_sesion
from .registry import TemplateRegistry
from .lifecycle import AgentLifecycle, LLMRefinerProtocol

# Singleton para el registro de plantillas (evita recarga constante)
_TEMPLATE_REGISTRY = TemplateRegistry(
    templates_root=os.path.join(os.path.dirname(__file__), "templates")
)

async def get_agent_refiner() -> LLMRefinerProtocol:
    """Provee el motor de refinamiento (Ollama por defecto)."""
    # Aquí podríamos inyectar OpenAI o AnthropicRefiner según configuración
    from .lifecycle import OllamaRefiner
    return OllamaRefiner()

async def get_agent_lifecycle(
    db: AsyncSession = Depends(obtener_sesion),
    refiner: LLMRefinerProtocol = Depends(get_agent_refiner)
) -> AgentLifecycle:
    """
    Inyector para FastAPI que proporciona una instancia lista de AgentLifecycle.
    """
    return AgentLifecycle(
        db=db,
        registry=_TEMPLATE_REGISTRY,
        refiner=refiner
    )
