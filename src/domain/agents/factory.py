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
        script_ventas: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Crea entidad de agente para persistencia en BD
        
        Args:
            agent_data: Datos del agente
            tenant_id: ID del tenant
            system_prompt: Prompt del sistema generado
            script_ventas: Scripts de ventas
            
        Returns:
            Dict con datos para inserción en BD
        """
        return {
            "id": str(uuid4()),
            "tenant_id": tenant_id,
            "name": agent_data.nombre,
            "area": agent_data.area,
            "descripcion": agent_data.descripcion,
            "genero": agent_data.genero.value,
            "humor": agent_data.humor.value,
            "personalidad": agent_data.personalidad,
            "idioma": agent_data.idioma,
            "tono": agent_data.tono.value,
            "coleccion_rag": agent_data.coleccion_rag,
            "tipo_negocio": agent_data.tipo_negocio,
            "objetivo": agent_data.objetivo,
            "instrucciones": agent_data.instrucciones,
            "modelo": agent_data.modelo,
            "temperatura": agent_data.temperatura,
            "max_tokens": agent_data.max_tokens,
            "canales": agent_data.canales,
            "horario_inicio": agent_data.horario_inicio,
            "horario_fin": agent_data.horario_fin,
            "dias_atencion": agent_data.dias_atencion,
            "mensaje_fuera_horario": agent_data.mensaje_fuera_horario,
            "script_ventas": json.dumps(script_ventas) if script_ventas else None,
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
        script_ventas: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        """Crea respuesta de agente para API
        
        Args:
            agent_id: ID del agente creado
            agent_data: Datos originales del agente
            system_prompt: Prompt generado
            script_ventas: Scripts generados
            
        Returns:
            AgentResponse para respuesta HTTP
        """
        return AgentResponse(
            id=agent_id,
            nombre=agent_data.nombre,
            area=agent_data.area,
            descripcion=agent_data.descripcion,
            genero=agent_data.genero,
            humor=agent_data.humor,
            personalidad=agent_data.personalidad,
            idioma=agent_data.idioma,
            tono=agent_data.tono,
            coleccion_rag=agent_data.coleccion_rag,
            tipo_negocio=agent_data.tipo_negocio,
            objetivo=agent_data.objetivo,
            instrucciones=agent_data.instrucciones,
            modelo=agent_data.modelo,
            temperatura=agent_data.temperatura,
            max_tokens=agent_data.max_tokens,
            canales=agent_data.canales,
            horario_inicio=agent_data.horario_inicio,
            horario_fin=agent_data.horario_fin,
            dias_atencion=agent_data.dias_atencion,
            mensaje_fuera_horario=agent_data.mensaje_fuera_horario,
            script_ventas=script_ventas,
            agent_type=agent_data.agent_type,
            specialty=agent_data.specialty,
            system_prompt=system_prompt,
            estado=AgentStatus.DRAFT,
            creado_en=None,  # Se asignará en BD
            actualizado_en=None
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
        script_ventas = data.get('script_ventas')
        if isinstance(script_ventas, str):
            try:
                script_ventas = json.loads(script_ventas)
            except json.JSONDecodeError:
                script_ventas = None
        
        # Parsear arrays si es necesario
        dias_atencion = data.get('dias_atencion')
        if isinstance(dias_atencion, str):
            try:
                dias_atencion = json.loads(dias_atencion)
            except json.JSONDecodeError:
                dias_atencion = []
        
        canales = data.get('canales')
        if isinstance(canales, str):
            try:
                canales = json.loads(canales)
            except json.JSONDecodeError:
                canales = []
        
        return AgentResponse(
            id=str(data.get('id')),
            nombre=data.get('name'),
            area=data.get('area'),
            descripcion=data.get('descripcion'),
            genero=AgentGender(data.get('genero', 'femenino')),
            humor=AgentTone(data.get('humor', 'profesional')),
            personalidad=data.get('personalidad'),
            idioma=data.get('idioma', 'Español (Ecuador)'),
            tono=AgentTone(data.get('tono', 'profesional')),
            coleccion_rag=data.get('coleccion_rag'),
            tipo_negocio=data.get('tipo_negocio'),
            objetivo=data.get('objetivo'),
            instrucciones=data.get('instrucciones'),
            modelo=data.get('modelo', 'qwen2.5:3b'),
            temperatura=float(data.get('temperatura', 0.7)),
            max_tokens=int(data.get('max_tokens', 512)),
            canales=canales or ['web_chat'],
            horario_inicio=data.get('horario_inicio'),
            horario_fin=data.get('horario_fin'),
            dias_atencion=dias_atencion,
            mensaje_fuera_horario=data.get('mensaje_fuera_horario'),
            script_ventas=script_ventas,
            agent_type=AgentType(data.get('agent_type', 'sales')),
            specialty=data.get('specialty'),
            system_prompt=data.get('system_prompt'),
            estado=AgentStatus(data.get('status', 'draft')),
            avatar_url=data.get('avatar_url'),
            creado_en=str(data.get('created_at')) if data.get('created_at') else None,
            actualizado_en=str(data.get('updated_at')) if data.get('updated_at') else None
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
            "nombre": "name",
            "area": "area",
            "descripcion": "descripcion",
            "genero": "genero",
            "humor": "humor",
            "personalidad": "personalidad",
            "idioma": "idioma",
            "tono": "tono",
            "coleccion_rag": "coleccion_rag",
            "tipo_negocio": "tipo_negocio",
            "objetivo": "objetivo",
            "instrucciones": "instrucciones",
            "modelo": "modelo",
            "temperatura": "temperatura",
            "max_tokens": "max_tokens",
            "canales": "canales",
            "horario_inicio": "horario_inicio",
            "horario_fin": "horario_fin",
            "dias_atencion": "dias_atencion",
            "mensaje_fuera_horario": "mensaje_fuera_horario",
            "script_ventas": "script_ventas",
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
