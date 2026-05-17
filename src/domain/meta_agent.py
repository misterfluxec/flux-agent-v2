from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from enum import Enum
from uuid import UUID, uuid4
from datetime import datetime

class ActionCategory(Enum):
    DATABASE = "database"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    INTEGRATION = "integration"

class AgentAction(BaseModel):
    """
    Representa una acción atómica que un agente puede realizar (Herramienta).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str
    category: ActionCategory
    parameters_schema: Dict[str, Any]
    required_capabilities: List[str] = []

class SOPStep(BaseModel):
    """
    Un paso individual dentro de un Procedimiento Estándar de Operación.
    """
    order: int
    instruction: str
    required_action: Optional[str] = None # Referencia al name de una AgentAction
    validation_criteria: str
    failure_protocol: str # Qué hacer si el paso falla

class SOP(BaseModel):
    """
    Standard Operating Procedure (SOP).
    Define la secuencia de pasos que un agente debe seguir para una tarea específica.
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    version: str
    description: str
    steps: List[SOPStep]
    trigger_conditions: List[str] = []

class BaseRole(BaseModel):
    """
    Define el Rol de un Agente (inspirado en MetaGPT).
    """
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    profile: str # Descripción del "persona"
    goals: List[str]
    constraints: List[str]
    allowed_actions: List[str] # Lista de nombres de AgentAction
    assigned_sops: List[str] # Lista de IDs de SOPs que este role puede ejecutar
    
    # Contexto específico del role
    context_template: str = ""

class AgentState(BaseModel):
    """
    Estado actual de un agente en ejecución.
    """
    role_id: str
    current_sop_id: Optional[str] = None
    current_step_index: int = 0
    memory_summary: str = ""
    last_updated: datetime = Field(default_factory=datetime.utcnow)
