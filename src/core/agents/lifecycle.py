# =============================================================================
# FLUXAGENT V2 — CICLO DE VIDA DEL AGENTE
# =============================================================================
# Módulo Profundo (Deep Module) que encapsula la "creación de vida" 
# de un agente IA, ocultando la complejidad de prompts, IA y persistencia.
# =============================================================================

import logging
import json
from uuid import UUID, uuid4
from typing import Dict, Any, Optional, Protocol, List
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field

from .registry import TemplateRegistry

logger = logging.getLogger(__name__)

# =============================================================================
# PROTOCOLOS E INTERFACES
# =============================================================================

class LLMRefinerProtocol(Protocol):
    """Interfaz para cualquier motor que pueda refinar un prompt."""
    async def refine(self, prompt: str, guidance: str, model: str = "qwen2.5:3b") -> str:
        ...

# =============================================================================
# IMPLEMENTACIONES CORE
# =============================================================================

class OllamaRefiner:
    """Refinador de prompts usando Ollama local."""
    
    async def refine(self, prompt: str, guidance: str, model: str = "qwen2.5:3b") -> str:
        from core.llm.router import llm_router
        
        refine_prompt = f"""
        Actúa como un Ingeniero de Prompts experto. Tu tarea es refinar el siguiente "System Prompt" para un agente de IA.
        
        REQUISITOS:
        1. Mantén todas las reglas de gobernanza y restricciones originales.
        2. Mejora la claridad, el tone profesional y la efectividad de las instructions.
        3. No añadidas introducciones, entrega directamente el prompt refinado.
        
        GUÍA DE REFINAMIENTO: {guidance}
        
        PROMPT ORIGINAL:
        ---
        {prompt}
        ---
        """
        try:
            resultado = await llm_router.generate(
                messages=[{"role": "user", "content": refine_prompt}],
                model=model,
                temperature=0.3 # Baja temperature para mantener fidelidad
            )
            texto = resultado if isinstance(resultado, str) else resultado.get("content", "")
            return texto.strip() if texto else prompt
        except Exception as e:
            logger.warning(f"Fallo en refinamiento IA (usando original): {e}")
            return prompt

# =============================================================================
# SERVICIO PRINCIPAL
# =============================================================================

class AgentLifecycle:
    """
    Gestiona el ciclo de vida completo de un agente.
    Punto de entrada único para la creación y actualización de agentes.
    """
    
    def __init__(
        self, 
        db: AsyncSession, 
        registry: TemplateRegistry, 
        refiner: Optional[LLMRefinerProtocol] = None
    ):
        self.db = db
        self.registry = registry
        self.refiner = refiner or OllamaRefiner()

    async def generate_identity(
        self, 
        descripcion_negocio: str, 
        agent_type: str, 
        tone: str
    ) -> str:
        """
        Genera una identidad base de sistema usando IA, 
        basada en la descripción del negocio.
        """
        prompt = f"""
        Eres un ingeniero de prompts experto creando la "Identidad de Sistema" para un agente de IA.
        Negocio: "{descripcion_negocio}"
        Tipo de Agente: {agent_type}
        Tono: {tone}

        Crea instructions en PRIMERA PERSONA ("Eres un asistente...").
        Incluye reglas de gobernanza: no inventar precios, consultar catálogo, escalación humana.
        """
        # Usamos el refiner interno (que a su vez usa el llm_router)
        # Pasamos un guidance vacío porque ya está en el prompt principal
        return await self.refiner.refine(prompt, "Genera una identidad única y profesional.")

    async def create_agent(
        self, 
        tenant_id: UUID, 
        agent_data: Dict[str, Any], 
        auto_refine: bool = False
    ) -> Dict[str, Any]:
        """
        Crea un agente completo: valida, renderiza, refina y persiste.
        """
        # 1. Verificar límites de tenant (Aislamiento y Reglas de Negocio)
        await self._check_tenant_limits(tenant_id)
        
        agent_type = agent_data.get("agent_type", "sales")
        
        # 2. Generar System Prompt (vía TemplateRegistry)
        # Extraemos solo lo necesario para el renderizado
        base_prompt = self.registry.render(agent_type, agent_data)
        
        # 3. Refinamiento opcional con IA
        system_prompt = base_prompt
        if auto_refine:
            guidance = agent_data.get("personality", "Tono profesional y eficiente.")
            system_prompt = await self.refiner.refine(base_prompt, guidance)

        # 4. Generar Script de Ventas (Lógica de dominio)
        # Esto podría ser un módulo aparte en el futuro si crece
        sales_script = self._generate_default_script(agent_type, agent_data)
        
        # 5. Persistencia (pgvector habilitado vía base SQL)
        nuevo_id = uuid4()
        
        # Mapeo de campos para la BD (normalización)
        params = {
            "id": str(nuevo_id),
            "tid": str(tenant_id),
            "name": agent_data.get("name", "Nuevo Agente"),
            "area": self._map_area(agent_type),
            "desc": agent_data.get("description", ""),
            "gen": agent_data.get("gender", "femenino"),
            "hum": agent_data.get("mood", "profesional"),
            "pers": agent_data.get("personality", ""),
            "language": agent_data.get("language", "Español"),
            "tone": agent_data.get("tone", "profesional"),
            "coleccion": agent_data.get("rag_collection"),
            "type": agent_data.get("business_type"),
            "objective": agent_data.get("objective"),
            "instr": agent_data.get("instructions"),
            "model": agent_data.get("model", "qwen2.5:3b"),
            "temp": agent_data.get("temperature", 0.7),
            "tokens": agent_data.get("max_tokens", 512),
            "channels": agent_data.get("channels", ["web_chat"]),
            "script": json.dumps(sales_script),
            "atype": agent_type,
            "specialty": agent_data.get("specialty"),
            "sys_prompt": system_prompt,
            "status": "is_active"
        }

        await self.db.execute(
            text("""
                INSERT INTO agents (
                    id, tenant_id, name, area, description, gender, mood, personality,
                    language, tone, rag_collection, business_type, objective, instructions,
                    model, temperature, max_tokens, channels, sales_script,
                    agent_type, specialty, system_prompt, status
                ) VALUES (
                    :id, :tid, :name, :area, :desc, :gen, :hum, :pers,
                    :language, :tone, :coleccion, :type, :objective, :instr,
                    :model, :temp, :tokens, :channels, :script,
                    :atype, :specialty, :sys_prompt, :status
                )
            """),
            params
        )
        
        # El commit lo maneja quien inyecta la sesión o nosotros si somos el dueño
        # En este patrón, el servicio suele hacer commit si es una operación atómica
        await self.db.commit()
        
        return {
            "id": str(nuevo_id),
            "system_prompt": system_prompt,
            "sales_script": sales_script
        }

    async def _check_tenant_limits(self, tenant_id: UUID):
        """Valida que el tenant no haya superado su cuota de agentes."""
        result = await self.db.execute(
            text("SELECT max_agents FROM tenants WHERE id = :tid"),
            {"tid": str(tenant_id)}
        )
        plan_row = result.fetchone()
        max_agents = plan_row.max_agents if plan_row else 1
        
        result_count = await self.db.execute(
            text("SELECT COUNT(*) FROM agents WHERE tenant_id = :tid"),
            {"tid": str(tenant_id)}
        )
        current_count = result_count.scalar() or 0
        
        if current_count >= max_agents:
            raise ValueError(f"Límite de agentes alcanzado ({max_agents}).")

    def _generate_default_script(self, agent_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Genera un script de interacción base según el type."""
        # Esta lógica estaba antes en el router, ahora vive en el corazón del dominio.
        scripts = {
            "sales": {
                "fases": ["contacto", "calificacion", "presentacion", "cierre"],
                "reglas": ["siempre saludar", "identificar necesidad"],
                "escalacion": {"enabled": True, "keywords": ["gerente", "humano"]}
            },
            "support": {
                "fases": ["diagnostico", "solucion", "verificacion"],
                "reglas": ["paciencia", "claridad"],
                "escalacion": {"enabled": True, "keywords": ["ayuda", "error"]}
            }
        }
        return scripts.get(agent_type, scripts["sales"])

    def _map_area(self, agent_type: str) -> str:
        return {
            "sales": "Ventas",
            "support": "Soporte",
            "bookings": "Reservas",
            "custom": "General"
        }.get(agent_type, "General")
