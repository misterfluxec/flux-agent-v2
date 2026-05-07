# =============================================================================
# FLUXAGENT V2 — DOMAIN AGENTS SCHEMAS
# =============================================================================
# Schemas Pydantic para dominio de agentes
# Separados de routers para reutilización y testing
# =============================================================================

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AgentType(str, Enum):
    """Tipos de agentes soportados"""
    SALES = "sales"
    SUPPORT = "support"
    BOOKINGS = "bookings"
    CUSTOM = "custom"

class AgentStatus(str, Enum):
    """Estados de agentes"""
    DRAFT = "draft"
    TESTING = "testing"
    ACTIVE = "active"
    PAUSED = "paused"

class AgentGender(str, Enum):
    """Géneros para personalización"""
    MASCULINO = "masculino"
    FEMENINO = "femenino"
    NEUTRO = "neutro"

class AgentTone(str, Enum):
    """Tonos de comunicación"""
    PROFESIONAL = "profesional"
    AMIGABLE = "amigable"
    FORMAL = "formal"
    INFORMAL = "informal"
    DIVERTIDO = "divertido"

class AgentCreate(BaseModel):
    """Schema para creación de agentes"""
    nombre: str = Field(..., min_length=1, max_length=100, description="Nombre del agente")
    area: Optional[str] = Field(None, max_length=50, description="Área del agente")
    descripcion: Optional[str] = Field(None, max_length=500, description="Descripción del agente")
    genero: AgentGender = Field(AgentGender.FEMENINO, description="Género del agente")
    humor: AgentTone = Field(AgentTone.PROFESIONAL, description="Tono/humor del agente")
    personalidad: Optional[str] = Field(None, max_length=1000, description="Personalidad del agente")
    idioma: str = Field("Español (Ecuador)", max_length=50, description="Idioma del agente")
    tono: AgentTone = Field(AgentTone.PROFESIONAL, description="Tono de comunicación")
    coleccion_rag: Optional[str] = Field(None, description="Colección RAG asociada")
    tipo_negocio: Optional[str] = Field(None, max_length=100, description="Tipo de negocio")
    objetivo: Optional[str] = Field(None, max_length=500, description="Objetivo del agente")
    instrucciones: Optional[str] = Field(None, max_length=2000, description="Instrucciones específicas")
    modelo: str = Field("qwen2.5:3b", description="Modelo LLM a usar")
    temperatura: float = Field(0.7, ge=0.0, le=2.0, description="Temperatura del modelo")
    max_tokens: int = Field(512, ge=1, le=4096, description="Tokens máximos de respuesta")
    canales: List[str] = Field(default=["web_chat"], description="Canales habilitados")
    horario_inicio: Optional[str] = Field("08:00", description="Hora de inicio de atención")
    horario_fin: Optional[str] = Field("20:00", description="Hora de fin de atención")
    dias_atencion: Optional[List[str]] = Field(None, description="Días de atención")
    mensaje_fuera_horario: Optional[str] = Field(None, max_length=300, description="Mensaje fuera de horario")
    script_ventas: Optional[Dict[str, Any]] = Field(None, description="Scripts de ventas")
    agent_type: AgentType = Field(AgentType.SALES, description="Tipo de agente")
    specialty: Optional[str] = Field(None, max_length=100, description="Especialidad del agente")
    system_prompt: Optional[str] = Field(None, max_length=5000, description="Prompt del sistema")

    @validator('horario_inicio', 'horario_fin')
    def validate_time_format(cls, v):
        """Valida formato HH:MM"""
        if v and len(v) == 5:
            try:
                hours, minutes = v.split(':')
                if 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59:
                    return v
            except ValueError:
                pass
        raise ValueError('Formato de hora inválido. Use HH:MM')

    @validator('dias_atencion')
    def validate_dias_atencion(cls, v):
        """Valida días de la semana"""
        if v:
            valid_days = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
            invalid_days = [d for d in v if d.lower() not in valid_days]
            if invalid_days:
                raise ValueError(f'Días inválidos: {invalid_days}')
        return v

    class Config:
        use_enum_values = True

class AgentUpdate(BaseModel):
    """Schema para actualización de agentes"""
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)
    area: Optional[str] = Field(None, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=500)
    genero: Optional[AgentGender] = None
    humor: Optional[AgentTone] = None
    personalidad: Optional[str] = Field(None, max_length=1000)
    idioma: Optional[str] = Field(None, max_length=50)
    tono: Optional[AgentTone] = None
    coleccion_rag: Optional[str] = None
    tipo_negocio: Optional[str] = Field(None, max_length=100)
    objetivo: Optional[str] = Field(None, max_length=500)
    instrucciones: Optional[str] = Field(None, max_length=2000)
    modelo: Optional[str] = None
    temperatura: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    canales: Optional[List[str]] = None
    horario_inicio: Optional[str] = None
    horario_fin: Optional[str] = None
    dias_atencion: Optional[List[str]] = None
    mensaje_fuera_horario: Optional[str] = Field(None, max_length=300)
    script_ventas: Optional[Dict[str, Any]] = None
    agent_type: Optional[AgentType] = None
    specialty: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = Field(None, max_length=5000)

    @validator('horario_inicio', 'horario_fin')
    def validate_time_format(cls, v):
        if v and len(v) == 5:
            try:
                hours, minutes = v.split(':')
                if 0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59:
                    return v
            except ValueError:
                pass
        raise ValueError('Formato de hora inválido. Use HH:MM')

    class Config:
        use_enum_values = True

class AgentResponse(BaseModel):
    """Schema para respuesta de agentes"""
    id: str
    nombre: str
    area: Optional[str]
    descripcion: Optional[str]
    genero: AgentGender
    humor: AgentTone
    personalidad: Optional[str]
    idioma: str
    tono: AgentTone
    coleccion_rag: Optional[str]
    tipo_negocio: Optional[str]
    objetivo: Optional[str]
    instrucciones: Optional[str]
    modelo: str
    temperatura: float
    max_tokens: int
    canales: List[str]
    horario_inicio: Optional[str]
    horario_fin: Optional[str]
    dias_atencion: Optional[List[str]]
    mensaje_fuera_horario: Optional[str]
    script_ventas: Optional[Dict[str, Any]]
    agent_type: AgentType
    specialty: Optional[str]
    system_prompt: Optional[str]
    estado: AgentStatus
    avatar_url: Optional[str] = None
    creado_en: Optional[str] = None
    actualizado_en: Optional[str] = None

    class Config:
        use_enum_values = True

class AgentStats(BaseModel):
    """Schema para estadísticas de agente"""
    agent_id: str
    agent_name: str
    total_conversations: int
    total_messages: int
    total_sales: float
    conversion_rate: float
    avg_response_time: float
    satisfaction_score: float

class AgentConfig(BaseModel):
    """Schema para configuración de agente"""
    agent_type: AgentType
    model_config: Dict[str, Any]
    channel_config: Dict[str, Any]
    rag_config: Optional[Dict[str, Any]] = None
    custom_settings: Optional[Dict[str, Any]] = None
