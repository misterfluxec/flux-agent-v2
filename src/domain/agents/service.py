# =============================================================================
# FLUXAGENT V2 — DOMAIN AGENTS SERVICE
# =============================================================================
# Lógica de negocio centralizada para gestión de agentes
# Separación de infraestructura (routers, DB) y dominio
# =============================================================================

from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import logging

from .schemas import AgentCreate, AgentUpdate, AgentResponse, AgentType, AgentStatus
from .prompts import AgentPromptFactory
from .factory import AgentFactory

logger = logging.getLogger(__name__)

class AgentService:
    """Servicio de dominio para gestión de agentes IA"""
    
    def __init__(self, db_session):
        """Inicializa servicio con sesión de base de datos"""
        self.db = db_session
    
    async def create_agent(self, agent_data: AgentCreate, tenant_id: str) -> AgentResponse:
        """Crea nuevo agente con lógica de negocio completa
        
        Args:
            agent_data: Datos del agente a crear
            tenant_id: ID del tenant
            
        Returns:
            AgentResponse: Agente creado
            
        Raises:
            ValueError: Si hay error de validación
            Exception: Si hay error en BD
        """
        try:
            # 1. Validaciones de negocio
            await self._validate_agent_creation(agent_data, tenant_id)
            
            # 2. Generar prompts y scripts
            system_prompt, sales_script = AgentPromptFactory.create_system_prompt(
                agent_type=agent_data.agent_type,
                personality=agent_data.personality,
                instructions=agent_data.instructions,
                specialty=agent_data.specialty,
                sales_script=agent_data.sales_script
            )
            
            # 3. Crear entidad agente
            agent_entity = AgentFactory.create_entity(
                agent_data=agent_data,
                tenant_id=tenant_id,
                system_prompt=system_prompt,
                sales_script=sales_script
            )
            
            # 4. Persistir en base de datos
            agent_id = await self._persist_agent(agent_entity)
            
            # 5. Retornar respuesta
            return AgentFactory.create_response(
                agent_id=agent_id,
                agent_data=agent_data,
                system_prompt=system_prompt,
                sales_script=sales_script
            )
            
        except Exception as e:
            logger.error(f"Error creando agente: {e}")
            raise
    
    async def update_agent(self, agent_id: str, update_data: AgentUpdate, tenant_id: str) -> AgentResponse:
        """Actualiza agente existente
        
        Args:
            agent_id: ID del agente a actualizar
            update_data: Datos a actualizar
            tenant_id: ID del tenant
            
        Returns:
            AgentResponse: Agente actualizado
        """
        try:
            # 1. Obtener agente existente
            existing_agent = await self._get_agent_by_id(agent_id, tenant_id)
            if not existing_agent:
                raise ValueError(f"Agente {agent_id} no encontrado")
            
            # 2. Validar actualización
            await self._validate_agent_update(update_data, existing_agent)
            
            # 3. Regenerar prompts si cambió type o configuración
            system_prompt, sales_script = await self._regenerate_prompts_if_needed(
                existing_agent, update_data
            )
            
            # 4. Actualizar en BD
            await self._update_agent_in_db(agent_id, update_data, system_prompt, sales_script)
            
            # 5. Retornar respuesta actualizada
            return await self._get_agent_response(agent_id)
            
        except Exception as e:
            logger.error(f"Error actualizando agente {agent_id}: {e}")
            raise
    
    async def list_agents(self, tenant_id: str, status: Optional[AgentStatus] = None) -> List[AgentResponse]:
        """Lista agentes del tenant con filtros opcionales
        
        Args:
            tenant_id: ID del tenant
            status: Filtro por status (opcional)
            
        Returns:
            List[AgentResponse]: Lista de agentes
        """
        try:
            query = "SELECT * FROM agents WHERE tenant_id = :tenant_id"
            params = {"tenant_id": tenant_id}
            
            if status:
                query += " AND status = :status"
                params["status"] = status.value
            
            query += " ORDER BY created_at DESC"
            
            result = await self.db.execute(query, params)
            agents = []
            
            for row in result:
                agent_response = AgentFactory.create_response_from_db_row(row)
                agents.append(agent_response)
            
            return agents
            
        except Exception as e:
            logger.error(f"Error listando agentes: {e}")
            raise
    
    async def get_agent(self, agent_id: str, tenant_id: str) -> Optional[AgentResponse]:
        """Obtiene agente específico
        
        Args:
            agent_id: ID del agente
            tenant_id: ID del tenant
            
        Returns:
            Optional[AgentResponse]: Agente encontrado o None
        """
        try:
            return await self._get_agent_response(agent_id, tenant_id)
        except Exception as e:
            logger.error(f"Error obteniendo agente {agent_id}: {e}")
            return None
    
    async def delete_agent(self, agent_id: str, tenant_id: str) -> bool:
        """Elimina agente (soft delete)
        
        Args:
            agent_id: ID del agente
            tenant_id: ID del tenant
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            # Verificar que existe y pertenece al tenant
            existing_agent = await self._get_agent_by_id(agent_id, tenant_id)
            if not existing_agent:
                raise ValueError(f"Agente {agent_id} no encontrado")
            
            # Soft delete: cambiar status a 'paused'
            await self.db.execute(
                "UPDATE agents SET status = :status, updated_at = NOW() WHERE id = :agent_id",
                {"status": AgentStatus.PAUSED.value, "agent_id": agent_id}
            )
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando agente {agent_id}: {e}")
            return False
    
    async def change_agent_status(self, agent_id: str, new_status: AgentStatus, tenant_id: str) -> bool:
        """Cambia status de agente
        
        Args:
            agent_id: ID del agente
            new_status: Nuevo status
            tenant_id: ID del tenant
            
        Returns:
            bool: True si se cambió correctamente
        """
        try:
            # Verificar que existe y pertenece al tenant
            existing_agent = await self._get_agent_by_id(agent_id, tenant_id)
            if not existing_agent:
                raise ValueError(f"Agente {agent_id} no encontrado")
            
            # Validar transición de estados
            await self._validate_status_transition(existing_agent.get('status'), new_status)
            
            # Actualizar status
            await self.db.execute(
                "UPDATE agents SET status = :status, updated_at = NOW() WHERE id = :agent_id",
                {"status": new_status.value, "agent_id": agent_id}
            )
            
            await self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error cambiando status agente {agent_id}: {e}")
            return False
    
    # Métodos privados de validación y persistencia
    
    async def _validate_agent_creation(self, agent_data: AgentCreate, tenant_id: str):
        """Validaciones para creación de agente"""
        # Verificar límite de agentes por plan
        from core.plan_manager import PlanManager
        plan_manager = PlanManager()
        
        current_agents = await self._count_agents_by_tenant(tenant_id)
        max_agents = await plan_manager.get_max_agents(tenant_id)
        
        if current_agents >= max_agents:
            raise ValueError(f"Límite de agentes alcanzado ({max_agents})")
        
        # Verificar name único en tenant
        existing = await self.db.execute(
            "SELECT id FROM agents WHERE tenant_id = :tid AND name = :name",
            {"tid": tenant_id, "name": agent_data.name}
        )
        
        if existing.fetchone():
            raise ValueError(f"Ya existe un agente con name '{agent_data.name}'")
    
    async def _validate_agent_update(self, update_data: AgentUpdate, existing_agent: Dict[str, Any]):
        """Validaciones para actualización de agente"""
        if update_data.name:
            # Verificar que nuevo name no exista (excluyendo actual)
            existing = await self.db.execute(
                "SELECT id FROM agents WHERE tenant_id = :tid AND name = :name AND id != :agent_id",
                {
                    "tid": existing_agent.get('tenant_id'),
                    "name": update_data.name,
                    "agent_id": existing_agent.get('id')
                }
            )
            
            if existing.fetchone():
                raise ValueError(f"Ya existe un agente con name '{update_data.name}'")
    
    async def _validate_status_transition(self, current_status: str, new_status: AgentStatus):
        """Valida que la transición de estados sea válida"""
        # Lógica de validación de transiciones
        invalid_transitions = {
            AgentStatus.DRAFT: [],  # Puede ir a cualquier status
            AgentStatus.TESTING: [AgentStatus.DRAFT],
            AgentStatus.ACTIVE: [AgentStatus.DRAFT],
            AgentStatus.PAUSED: []
        }
        
        if new_status.value in invalid_transitions.get(current_status, []):
            raise ValueError(f"Transición inválida de {current_status} a {new_status.value}")
    
    async def _persist_agent(self, agent_entity: Dict[str, Any]) -> str:
        """Persiste agente en base de datos"""
        await self.db.execute(
            """
            INSERT INTO agents (
                id, tenant_id, name, area, description, gender, mood, personality,
                language, tone, rag_collection, business_type, objective, instructions,
                model, temperature, max_tokens, channels, schedule_start, schedule_end,
                service_days, off_hours_message, sales_script, agent_type,
                specialty, system_prompt, status
            ) VALUES (
                :id, :tenant_id, :name, :area, :description, :gender, :mood, :personality,
                :language, :tone, :rag_collection, :business_type, :objective, :instructions,
                :model, :temperature, :max_tokens, :channels, :schedule_start, :schedule_end,
                :service_days, :off_hours_message, :sales_script, :agent_type,
                :specialty, :system_prompt, :status
            )
            """,
            agent_entity
        )
        
        await self.db.commit()
        return agent_entity['id']
    
    async def _get_agent_by_id(self, agent_id: str, tenant_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene agente por ID y tenant"""
        result = await self.db.execute(
            "SELECT * FROM agents WHERE id = :agent_id AND tenant_id = :tenant_id",
            {"agent_id": agent_id, "tenant_id": tenant_id}
        )
        return result.fetchone()._mapping if result.fetchone() else None
    
    async def _get_agent_response(self, agent_id: str, tenant_id: str) -> AgentResponse:
        """Obtiene AgentResponse desde BD"""
        result = await self.db.execute(
            "SELECT * FROM agents WHERE id = :agent_id AND tenant_id = :tenant_id",
            {"agent_id": agent_id, "tenant_id": tenant_id}
        )
        row = result.fetchone()
        
        if not row:
            raise ValueError(f"Agente {agent_id} no encontrado")
        
        return AgentFactory.create_response_from_db_row(row)
    
    async def _count_agents_by_tenant(self, tenant_id: str) -> int:
        """Cuenta agentes activos de un tenant"""
        result = await self.db.execute(
            "SELECT COUNT(*) FROM agents WHERE tenant_id = :tenant_id",
            {"tenant_id": tenant_id}
        )
        return int(result.fetchone()[0])
    
    async def _regenerate_prompts_if_needed(
        self, 
        existing_agent: Dict[str, Any], 
        update_data: AgentUpdate
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Regenera prompts si cambió configuración relevante"""
        # Si cambió type, personality, instructions o especialidad
        should_regenerate = any([
            update_data.agent_type,
            update_data.personality,
            update_data.instructions,
            update_data.specialty,
            update_data.sales_script
        ])
        
        if should_regenerate:
            # Combinar datos existentes con actualizaciones
            combined_data = {
                "agent_type": update_data.agent_type or existing_agent.get('agent_type'),
                "personality": update_data.personality or existing_agent.get('personality'),
                "instructions": update_data.instructions or existing_agent.get('instructions'),
                "specialty": update_data.specialty or existing_agent.get('specialty'),
                "sales_script": update_data.sales_script or existing_agent.get('sales_script')
            }
            
            return AgentPromptFactory.create_system_prompt(**combined_data)
        
        # Retornar prompts existentes
        return existing_agent.get('system_prompt'), existing_agent.get('sales_script')
    
    async def _update_agent_in_db(
        self, 
        agent_id: str, 
        update_data: AgentUpdate, 
        system_prompt: str, 
        sales_script: Optional[Dict[str, Any]]
    ):
        """Actualiza agente en base de datos"""
        update_fields = []
        params = {"agent_id": agent_id, "system_prompt": system_prompt}
        
        # Construir campos dinámicamente
        if update_data.name:
            update_fields.append("name = :name")
            params["name"] = update_data.name
        # ... agregar otros campos
        
        if sales_script:
            update_fields.append("sales_script = :sales_script")
            params["sales_script"] = sales_script
        
        update_fields.append("updated_at = NOW()")
        
        query = f"UPDATE agents SET {', '.join(update_fields)} WHERE id = :agent_id"
        await self.db.execute(query, params)
        await self.db.commit()
