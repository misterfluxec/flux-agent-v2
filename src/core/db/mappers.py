# =============================================================================
# FLUXAGENT V2 — DB MAPPERS
# =============================================================================
# Mapeo entre columnas de base de datos (inglés) y schemas backend (español)
# Resuelve inconsistencias entre DB y backend
# =============================================================================

from typing import Dict, Any, Optional, TypeVar, Generic
from datetime import datetime
from dataclasses import dataclass

T = TypeVar('T')

@dataclass
class FieldMapping:
    """Configuración de mapeo de campo"""
    db_field: str
    backend_field: str
    transform: Optional[callable] = None
    
class BaseMapper(Generic[T]):
    """Base para mappers de entidades"""
    
    # Mapeo DB -> Backend
    DB_TO_BACKEND: Dict[str, str] = {}
    
    # Mapeo Backend -> DB  
    BACKEND_TO_DB: Dict[str, str] = {}
    
    # Transformaciones especiales
    TRANSFORMS: Dict[str, callable] = {}
    
    @classmethod
    def to_backend(cls, db_row: Any) -> Dict[str, Any]:
        """Convierte row de DB a dict para backend
        
        Args:
            db_row: Row de SQLAlchemy o similar
            
        Returns:
            Dict con nombres de campos del backend
        """
        if not db_row:
            return {}
            
        result = {}
        
        # Obtener mapping del row ( SQLAlchemy 2.0 )
        if hasattr(db_row, '_mapping'):
            row_dict = db_row._mapping
        elif hasattr(db_row, '__dict__'):
            row_dict = db_row.__dict__
        else:
            # Fallback para tuples/dicts
            row_dict = db_row if isinstance(db_row, dict) else {}
        
        for db_field, value in row_dict.items():
            # Saltar campos internos de SQLAlchemy
            if db_field.startswith('_'):
                continue
                
            # Mapear nombre de campo
            backend_field = cls.DB_TO_BACKEND.get(db_field, db_field)
            
            # Aplicar transformación si existe
            if backend_field in cls.TRANSFORMS:
                value = cls.TRANSFORMS[backend_field](value)
            
            result[backend_field] = value
            
        return result
    
    @classmethod
    def to_db(cls, backend_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convierte dict de backend a columnas DB
        
        Args:
            backend_data: Dict con nombres de campos del backend
            
        Returns:
            Dict con nombres de columnas de DB
        """
        result = {}
        
        for backend_field, value in backend_data.items():
            if value is None:
                continue
                
            # Mapear nombre de campo
            db_field = cls.BACKEND_TO_DB.get(backend_field, backend_field)
            
            result[db_field] = value
            
        return result

class AgentMapper(BaseMapper):
    """Mapea entre columnas agents (inglés) y schemas backend (español)"""
    
    DB_TO_BACKEND = {
        "id": "id",
        "tenant_id": "tenant_id",
        "name": "nombre",
        "avatar_url": "avatar_url",
        "agent_type": "agent_type",
        "specialty": "specialty",
        "system_prompt": "system_prompt",
        "tone": "tono",
        "temperature": "temperatura",
        "max_tokens": "max_tokens",
        "status": "estado",
        "created_at": "creado_en",
        "updated_at": "actualizado_en",
        # Campos adicionales de la tabla extendida
        "area": "area",
        "descripcion": "descripcion",
        "genero": "genero",
        "humor": "humor",
        "personalidad": "personalidad",
        "idioma": "idioma",
        "coleccion_rag": "coleccion_rag",
        "tipo_negocio": "tipo_negocio",
        "objetivo": "objetivo",
        "instrucciones": "instrucciones",
        "modelo": "modelo",
        "canales": "canales",
        "horario_inicio": "horario_inicio",
        "horario_fin": "horario_fin",
        "dias_atencion": "dias_atencion",
        "mensaje_fuera_horario": "mensaje_fuera_horario",
        "script_ventas": "script_ventas",
    }
    
    BACKEND_TO_DB = {v: k for k, v in DB_TO_BACKEND.items()}
    
    TRANSFORMS = {
        "creado_en": lambda x: str(x) if x else None,
        "actualizado_en": lambda x: str(x) if x else None,
        "script_ventas": lambda x: x if isinstance(x, (dict, list)) else {},
        "dias_atencion": lambda x: x if isinstance(x, list) else [],
        "canales": lambda x: x if isinstance(x, list) else [],
    }

class ConversationMapper(BaseMapper):
    """Mapea entre columnas conversations (inglés) y backend (español)"""
    
    DB_TO_BACKEND = {
        "id": "id",
        "tenant_id": "tenant_id",
        "agent_id": "agent_id",
        "customer_id": "customer_id",
        "status": "estado",
        "started_at": "iniciada_en",
        "ended_at": "finalizada_en",
        "last_message_at": "ultimo_mensaje_en",
        "total_messages": "total_mensajes",
        "revenue_generated": "valor_venta",
        "sale_closed": "venta_cerrada",
        "sentiment": "sentimiento",
        "created_at": "creado_en",
        "updated_at": "actualizado_en",
    }
    
    BACKEND_TO_DB = {v: k for k, v in DB_TO_BACKEND.items()}

class MessageMapper(BaseMapper):
    """Mapea entre columnas messages (inglés) y backend (español)"""
    
    DB_TO_BACKEND = {
        "id": "id",
        "tenant_id": "tenant_id",
        "conversation_id": "conversation_id",
        "sender_type": "tipo_emisor",
        "sender_id": "emisor_id",
        "content": "contenido",
        "message_type": "tipo_mensaje",
        "metadata": "metadatos",
        "created_at": "creado_en",
        "updated_at": "actualizado_en",
    }
    
    BACKEND_TO_DB = {v: k for k, v in DB_TO_BACKEND.items()}

class TenantMapper(BaseMapper):
    """Mapea entre columnas tenants (inglés) y backend (español)"""
    
    DB_TO_BACKEND = {
        "id": "id",
        "name": "nombre",
        "email": "email",
        "phone": "telefono",
        "plan": "plan",
        "status": "estado",
        "contract_start": "inicio_contrato",
        "contract_end": "fin_contrato",
        "max_agents": "max_agentes",
        "max_messages_month": "max_mensajes_mes",
        "messages_used_month": "mensajes_usados_mes",
        "max_whatsapp_instances": "max_instancias_whatsapp",
        "billing_info": "info_facturacion",
        "created_at": "creado_en",
        "updated_at": "actualizado_en",
    }
    
    BACKEND_TO_DB = {v: k for k, v in DB_TO_BACKEND.items()}

# Helper para mapeo automático
def map_to_backend(db_row: Any, mapper_class: type) -> Dict[str, Any]:
    """Helper para mapeo rápido"""
    return mapper_class.to_backend(db_row)

def map_to_db(backend_data: Dict[str, Any], mapper_class: type) -> Dict[str, Any]:
    """Helper para mapeo rápido"""
    return mapper_class.to_db(backend_data)

# Ejemplos de uso:
"""
# En router:
from core.db.mappers import AgentMapper, map_to_backend

# Mapear row de DB a response
row = await db.execute(query).fetchone()
agent_data = map_to_backend(row, AgentMapper)
return AgentResponse(**agent_data)

# Mapear datos de frontend a DB
db_data = map_to_db(agent.dict(), AgentMapper)
await db.execute(insert_query, db_data)
"""
