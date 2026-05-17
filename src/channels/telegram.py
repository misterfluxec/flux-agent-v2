"""
ADAPTER PARA TELEGRAM BOT API
=============================
Implementación para Telegram Bot.
"""

import httpx
import logging
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel

from channels.base import ChannelAdapter, Message, ChannelResponse

logger = logging.getLogger(__name__)


class TelegramAdapter(ChannelAdapter):
    """
    Adapter para Telegram Bot API.
    Requiere: bot_token (se pasa en el constructor o variable de entorno)
    """
    
    def __init__(self, bot_token: Optional[str] = None):
        self.bot_token = bot_token
        self._base_url = None
    
    @property
    def base_url(self) -> str:
        if self._base_url is None:
            if not self.bot_token:
                from config import obtener_config
                config = obtener_config()
                self.bot_token = getattr(config, 'telegram_bot_token', '')
            self._base_url = f"https://api.telegram.org/bot{self.bot_token}"
        return self._base_url
    
    @property
    def channel_name(self) -> str:
        return "telegram"
    
    async def verify_webhook(self, payload: Dict[str, Any]) -> bool:
        """Telegram no requiere verificación de webhook especial."""
        # El webhook de Telegram simplemente llega con el update
        return True
    
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Parsea webhook de Telegram."""
        update = payload.get("update", {})
        
        # Determinar type de mensaje
        message = update.get("message") or update.get("edited_message") or {}
        
        if not message:
            raise ValueError("No message in Telegram update")
        
        # Extraer contenido según type
        content_type = self._get_content_type(message)
        content = self._extract_content(message, content_type)
        
        from_info = message.get("from", {})
        chat_info = message.get("chat", {})
        
        return Message(
            channel=self.channel_name,
            external_id=str(message.get("message_id", "")),
            sender_id=str(from_info.get("id", "")),
            sender_name=from_info.get("first_name", ""),
            content_type=content_type,
            content=content,
            timestamp=float(message.get("date", 0)),
            metadata={
                "chat_id": str(chat_info.get("id", "")),
                "chat_type": chat_info.get("type", ""),
                "username": from_info.get("username", ""),
                "is_bot": from_info.get("is_bot", False)
            }
        )
    
    def _get_content_type(self, message: dict) -> str:
        """Determina el type de contenido del mensaje."""
        if "text" in message:
            return "text"
        elif "voice" in message:
            return "audio"
        elif "audio" in message:
            return "audio"
        elif "photo" in message:
            return "image"
        elif "video" in message:
            return "video"
        elif "document" in message:
            return "document"
        elif "video_note" in message:
            return "video"  # Video circular
        elif "sticker" in message:
            return "image"
        elif "location" in message:
            return "location"
        elif "contact" in message:
            return "contacts"
        return "text"
    
    def _extract_content(self, message: dict, content_type: str) -> Union[str, Dict[str, Any]]:
        """Extrae el contenido según el type."""
        if content_type == "text":
            return message.get("text", "")
        
        elif content_type == "audio":
            return {
                "file_id": message.get("voice", {}).get("file_id") or message.get("audio", {}).get("file_id"),
                "duration": message.get("voice", {}).get("duration") or message.get("audio", {}).get("duration"),
                "mime_type": message.get("audio", {}).get("mime_type")
            }
        
        elif content_type == "image":
            photo = message.get("photo", [])
            if photo:
                return {
                    "file_id": photo[-1].get("file_id"),
                    "width": photo[-1].get("width"),
                    "height": photo[-1].get("height")
                }
            sticker = message.get("sticker", {})
            return {
                "file_id": sticker.get("file_id"),
                "is_animated": sticker.get("is_animated", False)
            }
        
        elif content_type == "video":
            video = message.get("video", {})
            return {
                "file_id": video.get("file_id"),
                "duration": video.get("duration"),
                "width": video.get("width"),
                "height": video.get("height")
            }
        
        elif content_type == "document":
            doc = message.get("document", {})
            return {
                "file_id": doc.get("file_id"),
                "file_name": doc.get("file_name"),
                "mime_type": doc.get("mime_type")
            }
        
        elif content_type == "location":
            location = message.get("location", {})
            return {
                "latitude": location.get("latitude"),
                "longitude": location.get("longitude")
            }
        
        return str(message)
    
    async def send_text(
        self, 
        recipient_id: str, 
        text: str, 
        reply_to: Optional[str] = None
    ) -> ChannelResponse:
        """Envía mensaje de texto."""
        if not self.bot_token:
            return ChannelResponse(
                success=False,
                error="Telegram bot token not configured"
            )
        
        params = {
            "chat_id": recipient_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        if reply_to:
            params["reply_to_message_id"] = reply_to
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendMessage",
                    json=params
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("ok"):
                    msg_id = str(data.get("result", {}).get("message_id", ""))
                    return ChannelResponse(
                        success=True,
                        message_id=msg_id,
                        data=data
                    )
                else:
                    return ChannelResponse(
                        success=False,
                        error=data.get("description", "Unknown error")
                    )
        except Exception as e:
            logger.error(f"Error sending Telegram text: {e}")
            return ChannelResponse(success=False, error=str(e))
    
    async def send_media(
        self, 
        recipient_id: str, 
        media_type: str, 
        media_url_or_path: str, 
        caption: Optional[str] = None
    ) -> ChannelResponse:
        """Envía imagen/video/documento."""
        if not self.bot_token:
            return ChannelResponse(success=False, error="Telegram bot token not configured")
        
        # Determinar método según type
        method_map = {
            "image": "sendPhoto",
            "video": "sendVideo",
            "document": "sendDocument"
        }
        
        method = method_map.get(media_type, "sendPhoto")
        
        # Determinar si es URL o file_id
        if media_url_or_path.startswith("http"):
            payload = {
                "chat_id": recipient_id,
                media_type: media_url_or_path
            }
            if caption:
                payload["caption"] = caption
        else:
            # Enviar como archivo
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    with open(media_url_or_path, "rb") as f:
                        response = await client.post(
                            f"{self.base_url}/{method}",
                            data={"chat_id": recipient_id},
                            files={media_type: f}
                        )
                    response.raise_for_status()
                    data = response.json()
                    
                    if data.get("ok"):
                        return ChannelResponse(
                            success=True,
                            message_id=str(data.get("result", {}).get("message_id", "")),
                            data=data
                        )
            except Exception as e:
                return ChannelResponse(success=False, error=str(e))
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/{method}",
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                if data.get("ok"):
                    return ChannelResponse(
                        success=True,
                        message_id=str(data.get("result", {}).get("message_id", "")),
                        data=data
                    )
                return ChannelResponse(success=False, error=data.get("description"))
        except Exception as e:
            logger.error(f"Error sending Telegram media: {e}")
            return ChannelResponse(success=False, error=str(e))
    
    async def send_audio_note(
        self, 
        recipient_id: str, 
        audio_file_path: str
    ) -> ChannelResponse:
        """Envía nota de voz como voice message."""
        if not self.bot_token:
            return ChannelResponse(success=False, error="Telegram bot token not configured")
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(audio_file_path, "rb") as f:
                    response = await client.post(
                        f"{self.base_url}/sendVoice",
                        data={"chat_id": recipient_id},
                        files={"voice": f}
                    )
                response.raise_for_status()
                data = response.json()
                
                if data.get("ok"):
                    return ChannelResponse(
                        success=True,
                        message_id=str(data.get("result", {}).get("message_id", "")),
                        data=data
                    )
                return ChannelResponse(success=False, error=data.get("description"))
        except Exception as e:
            logger.error(f"Error sending Telegram voice: {e}")
            return ChannelResponse(success=False, error=str(e))
    
    async def send_typing_indicator(
        self, 
        recipient_id: str, 
        is_typing: bool
    ) -> bool:
        """Muestra indicador de 'escribiendo...'."""
        if not self.bot_token:
            return False
        
        action = "typing" if is_typing else "cancel"
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/sendChatAction",
                    json={
                        "chat_id": recipient_id,
                        "action": action
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Error sending typing indicator: {e}")
            return False
    
    async def mark_as_read(
        self, 
        recipient_id: str, 
        message_id: str
    ) -> bool:
        """Telegram no tiene función de marcar como leído."""
        return True