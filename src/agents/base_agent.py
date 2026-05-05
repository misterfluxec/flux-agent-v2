import logging
from dataclasses import dataclass, field
from typing import Optional, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

@dataclass
class MensajeChat:
    rol: str
    contenido: str

@dataclass
class ContextoAgente:
    tenant_id: UUID
    agent_id: Optional[UUID]
    session_id: str
    mensaje_usuario: str
    historial: list[MensajeChat] = field(default_factory=list)
    configuracion: dict = field(default_factory=dict)

@dataclass
class RespuestaAgente:
    contenido: str
    tokens_usados: int = 0
    modelo_usado: str = ""
    fuentes_rag: list[str] = field(default_factory=list)
    metadatos: dict = field(default_factory=dict)

class AgenteBase:
    def __init__(self, nombre: str = "Agente Base"):
        self.nombre = nombre
    
    async def cerrar(self):
        pass
    
    def construir_prompt_sistema(self, contexto: ContextoAgente) -> str:
        return ""
    
    async def procesar(self, contexto: ContextoAgente, sesion: Optional[AsyncSession] = None) -> RespuestaAgente:
        raise NotImplementedError
    
    async def procesar_streaming(self, contexto: ContextoAgente, sesion: Optional[AsyncSession] = None):
        raise NotImplementedError
