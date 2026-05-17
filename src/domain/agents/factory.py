# =============================================================================
# FLUXAGENT V2 — DOMAIN AGENTS FACTORY
# =============================================================================
# Factory para creación de entidades y respuestas de agentes
# Centraliza la lógica de construcción de objetos
# =============================================================================

from typing import Dict, Any, Optional
from uuid import uuid4
import json

from .schemas import AgentCreate, AgentResponse, AgentType, AgentStatus, AgentGender, AgentTone

class AgentFactory:
    """Factory para creación de entidades de agentes"""
    
    @staticmethod
    def create_entity(
        agent_data: AgentCreate,
        tenant_id: str,
        system_prompt: str,
        sales_script: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crea entidad de agente para persistencia en BD
        
        Args:
            agent_data: Datos del agente
            tenant_id: ID del tenant
            system_prompt: Prompt del sistema generado
            sales_script: Scripts de ventas
            
        Returns:
            Dict con datos para inserción en BD
        """
        return {
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": agent_data.name,
            "area": agent_data.area,
            "description": agent_data.description,
            "gender": agent_data.gender.value,
            "mood": agent_data.mood.value,
            "personality": agent_data.personality,
            "language": agent_data.language,
            "tone": agent_data.tone.value,
            "rag_collection": agent_data.rag_collection,
            "business_type": agent_data.business_type,
            "objective": agent_data.objective,
            "instructions": agent_data.instructions,
            "model": agent_data.model,
            "temperature": agent_data.temperature,
            "max_tokens": agent_data.max_tokens,
            "channels": agent_data.channels,
            "schedule_start": agent_data.schedule_start,
            "schedule_end": agent_data.schedule_end,
            "service_days": agent_data.service_days,
            "off_hours_message": agent_data.off_hours_message,
            "sales_script": json.dumps(sales_script) if sales_script else None,
            "agent_type": agent_data.agent_type.value,
            "specialty": agent_data.specialty,
            "system_prompt": system_prompt,
            "status": AgentStatus.DRAFT.value
        }
    
    @staticmethod
    def create_response(
        agent_id: str,
        agent_data: AgentCreate,
        system_prompt: str,
        sales_script: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Crea respuesta de agente para API
        
        Args:
            agent_id: ID del agente creado
            agent_data: Datos originales del agente
            system_prompt: Prompt generado
            sales_script: Scripts generados
            
        Returns:
            AgentResponse para respuesta HTTP
        """
        return AgentResponse(
            id=agent_id,
            name=agent_data.name,
            area=agent_data.area,
            description=agent_data.description,
            gender=agent_data.gender,
            mood=agent_data.mood,
            personality=agent_data.personality,
            language=agent_data.language,
            tone=agent_data.tone,
            rag_collection=agent_data.rag_collection,
            business_type=agent_data.business_type,
            objective=agent_data.objective,
            instructions=agent_data.instructions,
            model=agent_data.model,
            temperature=agent_data.temperature,
            max_tokens=agent_data.max_tokens,
            channels=agent_data.channels,
            schedule_start=agent_data.schedule_start,
            schedule_end=agent_data.schedule_end,
            service_days=agent_data.service_days,
            off_hours_message=agent_data.off_hours_message,
            sales_script=sales_script,
            agent_type=agent_data.agent_type,
            specialty=agent_data.specialty,
            system_prompt=system_prompt,
            status=AgentStatus.DRAFT,
            created_at=None,  # Se asignará en BD
            updated_at=None
        )
    
    @staticmethod
    def create_response_from_db_row(db_row) -> AgentResponse:
        """Crea AgentResponse desde row de base de datos
        
        Args:
            db_row: Row de SQLAlchemy con datos de agente
            
        Returns:
            AgentResponse con datos mapeados
        """
        # Obtener datos del row
        if hasattr(db_row, '_mapping'):
            data = db_row._mapping
        else:
            data = db_row.__dict__
        
        # Parsear JSON si es necesario
        sales_script = data.get('sales_script')
        if isinstance(sales_script, str):
            try:
                sales_script = json.loads(sales_script)
            except json.JSONDecodeError:
                sales_script = None
        
        # Parsear arrays si es necesario
        service_days = data.get('service_days')
        if isinstance(service_days, str):
            try:
                service_days = json.loads(service_days)
            except json.JSONDecodeError:
                service_days = []
        
        channels = data.get('channels')
        if isinstance(channels, str):
            try:
                channels = json.loads(channels)
            except json.JSONDecodeError:
                channels = []
        
        return AgentResponse(
            id=str(data.get('id')),
            name=data.get('name'),
            area=data.get('area'),
            description=data.get('description'),
            gender=AgentGender(data.get('gender', 'femenino')),
            mood=AgentTone(data.get('mood', 'profesional')),
            personality=data.get('personality'),
            language=data.get('language', 'Español (Ecuador)'),
            tone=AgentTone(data.get('tone', 'profesional')),
            rag_collection=data.get('rag_collection'),
            business_type=data.get('business_type'),
            objective=data.get('objective'),
            instructions=data.get('instructions'),
            model=data.get('model', 'qwen2.5:3b'),
            temperature=float(data.get('temperature', 0.7)),
            max_tokens=int(data.get('max_tokens', 512)),
            channels=channels or ['web_chat'],
            schedule_start=data.get('schedule_start'),
            schedule_end=data.get('schedule_end'),
            service_days=service_days,
            off_hours_message=data.get('off_hours_message'),
            sales_script=sales_script,
            agent_type=AgentType(data.get('agent_type', 'sales')),
            specialty=data.get('specialty'),
            system_prompt=data.get('system_prompt'),
            status=AgentStatus(data.get('status', 'draft')),
            avatar_url=data.get('avatar_url'),
            created_at=str(data.get('created_at')) if data.get('created_at') else None,
            updated_at=str(data.get('updated_at')) if data.get('updated_at') else None
        )
    
    @staticmethod
    def create_update_dict(update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea diccionario para actualización en BD
        
        Args:
            update_data: Datos de actualización
            
        Returns:
            Dict con campos mapeados para BD
        """
        update_dict = {}
        
        # Mapeo de campos backend -> BD
        field_mapping = {
            "name": "name",
            "area": "area",
            "description": "description",
            "gender": "gender",
            "mood": "mood",
            "personality": "personality",
            "language": "language",
            "tone": "tone",
            "rag_collection": "rag_collection",
            "business_type": "business_type",
            "objective": "objective",
            "instructions": "instructions",
            "model": "model",
            "temperature": "temperature",
            "max_tokens": "max_tokens",
            "channels": "channels",
            "schedule_start": "schedule_start",
            "schedule_end": "schedule_end",
            "service_days": "service_days",
            "off_hours_message": "off_hours_message",
            "sales_script": "sales_script",
            "agent_type": "agent_type",
            "specialty": "specialty",
            "system_prompt": "system_prompt"
        }
        
        for backend_field, value in update_data.items():
            if value is not None:
                db_field = field_mapping.get(backend_field, backend_field)
                
                # Manejar enums
                if hasattr(value, 'value'):
                    value = value.value
                
                # Manejar JSON
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                
                update_dict[db_field] = value
        
        return update_dict

class AgentConfigFactory:
    """Factory para configuraciones específicas de agentes"""
    
    @staticmethod
    def create_sales_config(specialty: Optional[str] = None) -> Dict[str, Any]:
        """Crea configuración base para agente de ventas"""
        base_config = {
            "model_config": {
                "temperature": 0.7,
                "max_tokens": 512,
                "model": "qwen2.5:3b"
            },
            "channel_config": {
                "web_chat": {"enabled": True},
                "whatsapp": {"enabled": False},
                "telegram": {"enabled": False}
            },
            "rag_config": {
                "enabled": True,
                "collection": None,
                "similarity_threshold": 0.7
            },
            "sales_config": {
                "follow_up_enabled": True,
                "escalation_enabled": True,
                "auto_response_delay": 2.0
            }
        }
        
        if specialty:
            base_config["sales_config"]["specialty"] = specialty
        
        return base_config
    
    @staticmethod
    def create_support_config(specialty: Optional[str] = None) -> Dict[str, Any]:
        """Crea configuración base para agente de soporte"""
        return {
            "model_config": {
                "temperature": 0.5,
                "max_tokens": 800,
                "model": "qwen2.5:3b"
            },
            "channel_config": {
                "web_chat": {"enabled": True},
                "whatsapp": {"enabled": True},
                "telegram": {"enabled": True}
            },
            "rag_config": {
                "enabled": True,
                "collection": "knowledge_base",
                "similarity_threshold": 0.8
            },
            "support_config": {
                "escalation_threshold": 3,
                "max_response_time": 60,
                "knowledge_base_priority": True
            }
        }
    
    @staticmethod
    def create_bookings_config(specialty: Optional[str] = None) -> Dict[str, Any]:
        """Crea configuración base para agente de reservas"""
        return {
            "model_config": {
                "temperature": 0.3,
                "max_tokens": 400,
                "model": "qwen2.5:3b"
            },
            "channel_config": {
                "web_chat": {"enabled": True},
                "whatsapp": {"enabled": True},
                "telegram": {"enabled": False}
            },
            "rag_config": {
                "enabled": True,
                "collection": "booking_info",
                "similarity_threshold": 0.9
            },
            "booking_config": {
                "auto_confirmation": True,
                "reminder_enabled": True,
                "cancellation_policy": "flexible"
            }
        }
