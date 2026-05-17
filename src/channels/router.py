"""
CHANNEL ROUTER - Factory Pattern
================================
Instancia el adapter correcto según el canal.
Permite extensión sin modificar código existente.
"""

from typing import Dict, Type, Optional, Any
from channels.base import ChannelAdapter, ChannelResponse, Message
from channels.whatsapp_cloud import WhatsAppCloudAdapter
from channels.telegram import TelegramAdapter
import logging

logger = logging.getLogger(__name__)


class ChannelRouter:
    """
    Factory que instancia el adapter correcto según el canal.
    
    Uso:
        adapter = ChannelRouter.get_adapter("whatsapp_cloud")
        message = await adapter.receive_message(payload)
    """
    
    _adapters: Dict[str, Type[ChannelAdapter]] = {
        "whatsapp_cloud": WhatsAppCloudAdapter,
        "telegram": TelegramAdapter,
    }
    
    _instances: Dict[str, ChannelAdapter] = {}
    
    @classmethod
    def register_adapter(
        cls, 
        channel_name: str, 
        adapter_class: Type[ChannelAdapter]
    ):
        """
        Registra un nuevo canal sin modificar código existente.
        Útil para agregar: messenger, instagram, slack, discord, etc.
        """
        cls._adapters[channel_name] = adapter_class
        # Limpiar instancia cache si existe
        cls._instances.pop(channel_name, None)
        logger.info(f"Registered new channel adapter: {channel_name}")
    
    @classmethod
    def get_adapter(
        cls, 
        channel_name: str, 
        force_new: bool = False,
        **kwargs
    ) -> ChannelAdapter:
        """
        Obtiene instancia del adapter configurado.
        
        Args:
            channel_name: Nombre del canal (whatsapp_cloud, telegram, etc)
            force_new: Si True, crea nueva instancia (para testing)
            **kwargs: Argumentos adicionales para el constructor
        """
        # Verificar si existe
        if channel_name not in cls._adapters:
            raise ValueError(
                f"Canal '{channel_name}' no registrado. "
                f"Canales disponibles: {list(cls._adapters.keys())}"
            )
        
        # Usar instancia cacheada si no es force_new
        if not force_new and channel_name in cls._instances:
            return cls._instances[channel_name]
        
        # Crear nueva instancia
        adapter_class = cls._adapters[channel_name]
        
        try:
            adapter = adapter_class(**kwargs)
            cls._instances[channel_name] = adapter
            logger.info(f"Created adapter instance for: {channel_name}")
            return adapter
        except Exception as e:
            logger.error(f"Error creating adapter for {channel_name}: {e}")
            raise
    
    @classmethod
    def list_supported_channels(cls) -> list[str]:
        """Retorna lista de channels disponibles."""
        return list(cls._adapters.keys())
    
    @classmethod
    def clear_cache(cls):
        """Limpia el cache de instancias."""
        cls._instances.clear()
        logger.info("Channel adapter cache cleared")
    
    @classmethod
    async def process_incoming(
        cls,
        channel_name: str,
        payload: Dict[str, Any],
        **kwargs
    ) -> Optional[Message]:
        """
        Procesa mensaje entrante de cualquier canal.
        Método de conveniencia.
        """
        try:
            adapter = cls.get_adapter(channel_name, **kwargs)
            message = await adapter.receive_message(payload)
            return message
        except Exception as e:
            logger.error(f"Error processing incoming message from {channel_name}: {e}")
            return None
    
    @classmethod
    async def send_response(
        cls,
        channel_name: str,
        recipient_id: str,
        text: str,
        audio_base64: Optional[str] = None,
        media_type: Optional[str] = None,
        media_url: Optional[str] = None,
        **kwargs
    ) -> ChannelResponse:
        """
        Envía respuesta estandarizada a cualquier canal.
        Maneja fallback automáticamente.
        """
        try:
            adapter = cls.get_adapter(channel_name, **kwargs)
            
            # Prioridad: Audio Note > Media > Texto
            if audio_base64:
                # Necesitamos guardar el audio temporalmente
                import tempfile
                import base64
                
                with tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=".mp3"
                ) as tmp:
                    tmp.write(base64.b64decode(audio_base64))
                    tmp_path = tmp.name
                
                result = await adapter.send_audio_note(recipient_id, tmp_path)
                
                # Limpiar archivo temporal
                import os
                os.unlink(tmp_path)
                
                if not result.success:
                    # Fallback a texto
                    return await adapter.send_text(recipient_id, text)
                return result
            
            elif media_type and media_url:
                return await adapter.send_media(
                    recipient_id, 
                    media_type, 
                    media_url
                )
            else:
                return await adapter.send_text(recipient_id, text)
                
        except Exception as e:
            logger.error(f"Error sending response via {channel_name}: {e}")
            return ChannelResponse(success=False, error=str(e))