"""
INTERFAZ BASE DEL CANAL - Adapter Pattern
==========================================
Contrato que todo adapter de canal debe implementar.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel


class Message(BaseModel):
    """
    Formato estandarizado de mensaje entrante.
    Todos los adapters deben convertir sus mensajes a este formato.
    """
    channel: str  # 'whatsapp', 'telegram', 'messenger'
    external_id: str  # ID único del mensaje en el canal
    sender_id: str  # ID del usuario
    sender_name: Optional[str] = None
    content_type: str  # 'text', 'image', 'audio', 'video', 'document'
    content: Union[str, Dict[str, Any]]  # Texto o metadata de media
    timestamp: float
    metadata: Dict[str, Any] = {}  # Datos extra del canal


class ChannelResponse(BaseModel):
    """Respuesta estándar de cualquier operación del canal."""
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    data: Dict[str, Any] = {}


class ChannelAdapter(ABC):
    """
    Contrato que todo adapter de canal debe implementar.
    Patrón: Adapter + Factory
    """
    
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Nombre identificador del canal."""
        pass
    
    @abstractmethod
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """
        Convierte webhook nativo → Message estandarizado.
        Debe manejar verification challenge si aplica.
        """
        pass
    
    @abstractmethod
    async def send_text(
        self, 
        recipient_id: str, 
        text: str, 
        reply_to: Optional[str] = None
    ) -> ChannelResponse:
        """Envía mensaje de texto."""
        pass
    
    @abstractmethod
    async def send_media(
        self, 
        recipient_id: str, 
        media_type: str, 
        media_url_or_path: str, 
        caption: Optional[str] = None
    ) -> ChannelResponse:
        """Envía imagen/audio/video/documento."""
        pass
    
    @abstractmethod
    async def send_audio_note(
        self, 
        recipient_id: str, 
        audio_file_path: str
    ) -> ChannelResponse:
        """Envía nota de voz (formato nativo del canal)."""
        pass
    
    @abstractmethod
    async def send_typing_indicator(
        self, 
        recipient_id: str, 
        is_typing: bool
    ) -> bool:
        """Muestra/oculta indicador de 'escribiendo...'."""
        pass
    
    @abstractmethod
    async def mark_as_read(
        self, 
        recipient_id: str, 
        message_id: str
    ) -> bool:
        """Marca mensaje como leído."""
        pass
    
    @abstractmethod
    async def verify_webhook(self, payload: Dict[str, Any]) -> bool:
        """Verifica si el webhook es válido (firma, token, etc)."""
        pass


class BaseChannelAdapter(ChannelAdapter):
    """Clase base con implementaciones comunes."""
    
    async def send_text(
        self, 
        recipient_id: str, 
        text: str, 
        reply_to: Optional[str] = None
    ) -> ChannelResponse:
        raise NotImplementedError()
    
    async def send_media(
        self, 
        recipient_id: str, 
        media_type: str, 
        media_url_or_path: str, 
        caption: Optional[str] = None
    ) -> ChannelResponse:
        raise NotImplementedError()
    
    async def send_audio_note(
        self, 
        recipient_id: str, 
        audio_file_path: str
    ) -> ChannelResponse:
        raise NotImplementedError()
    
    async def send_typing_indicator(
        self, 
        recipient_id: str, 
        is_typing: bool
    ) -> bool:
        return True
    
    async def mark_as_read(
        self, 
        recipient_id: str, 
        message_id: str
    ) -> bool:
        return True
    
    async def verify_webhook(self, payload: Dict[str, Any]) -> bool:
        return True