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
    name: str = Field(..., min_length=1, max_length=100, description="Nombre del agente")
    area: Optional[str] = Field(None, max_length=50, description="Área del agente")
    description: Optional[str] = Field(None, max_length=500, description="Descripción del agente")
    gender: AgentGender = Field(AgentGender.FEMENINO, description="Género del agente")
    mood: AgentTone = Field(AgentTone.PROFESIONAL, description="Tono/mood del agente")
    personality: Optional[str] = Field(None, max_length=1000, description="Personalidad del agente")
    language: str = Field("Español (Ecuador)", max_length=50, description="Idioma del agente")
    tone: AgentTone = Field(AgentTone.PROFESIONAL, description="Tono de comunicación")
    rag_collection: Optional[str] = Field(None, description="Colección RAG asociada")
    business_type: Optional[str] = Field(None, max_length=100, description="Tipo de negocio")
    objective: Optional[str] = Field(None, max_length=500, description="Objetivo del agente")
    instructions: Optional[str] = Field(None, max_length=2000, description="Instrucciones específicas")
    model: str = Field("qwen2.5:3b", description="Modelo LLM a usar")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Temperatura del model")
    max_tokens: int = Field(512, ge=1, le=4096, description="Tokens máximos de respuesta")
    channels: List[str] = Field(default=["web_chat"], description="Canales habilitados")
    schedule_start: Optional[str] = Field("08:00", description="Hora de inicio de atención")
    schedule_end: Optional[str] = Field("20:00", description="Hora de fin de atención")
    service_days: Optional[List[str]] = Field(None, description="Días de atención")
    off_hours_message: Optional[str] = Field(None, max_length=300, description="Mensaje fuera de horario")
    sales_script: Optional[Dict[str, Any]] = Field(None, description="Scripts de ventas")
    agent_type: AgentType = Field(AgentType.SALES, description="Tipo de agente")
    specialty: Optional[str] = Field(None, max_length=100, description="Especialidad del agente")
    system_prompt: Optional[str] = Field(None, max_length=5000, description="Prompt del sistema")

    @validator('schedule_start', 'schedule_end')
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

    @validator('service_days')
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
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    area: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    gender: Optional[AgentGender] = None
    mood: Optional[AgentTone] = None
    personality: Optional[str] = Field(None, max_length=1000)
    language: Optional[str] = Field(None, max_length=50)
    tone: Optional[AgentTone] = None
    rag_collection: Optional[str] = None
    business_type: Optional[str] = Field(None, max_length=100)
    objective: Optional[str] = Field(None, max_length=500)
    instructions: Optional[str] = Field(None, max_length=2000)
    model: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4096)
    channels: Optional[List[str]] = None
    schedule_start: Optional[str] = None
    schedule_end: Optional[str] = None
    service_days: Optional[List[str]] = None
    off_hours_message: Optional[str] = Field(None, max_length=300)
    sales_script: Optional[Dict[str, Any]] = None
    agent_type: Optional[AgentType] = None
    specialty: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = Field(None, max_length=5000)

    @validator('schedule_start', 'schedule_end')
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
    name: str
    area: Optional[str]
    description: Optional[str]
    gender: AgentGender
    mood: AgentTone
    personality: Optional[str]
    language: str
    tone: AgentTone
    rag_collection: Optional[str]
    business_type: Optional[str]
    objective: Optional[str]
    instructions: Optional[str]
    model: str
    temperature: float
    max_tokens: int
    channels: List[str]
    schedule_start: Optional[str]
    schedule_end: Optional[str]
    service_days: Optional[List[str]]
    off_hours_message: Optional[str]
    sales_script: Optional[Dict[str, Any]]
    agent_type: AgentType
    specialty: Optional[str]
    system_prompt: Optional[str]
    status: AgentStatus
    avatar_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

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
