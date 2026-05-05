"""
ADAPTER PARA WHATSAPP CLOUD API
==============================
Implementación oficial de WhatsApp Business Cloud API.
"""

import httpx
import base64
import logging
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel

from channels.base import ChannelAdapter, Message, ChannelResponse
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()


class WhatsAppCloudAdapter(ChannelAdapter):
    """
    Adapter para WhatsApp Cloud API.
    Requiere: WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN
    """
    
    def __init__(
        self,
        phone_number_id: Optional[str] = None,
        access_token: Optional[str] = None,
        verify_token: Optional[str] = None
    ):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = phone_number_id or getattr(config, 'whatsapp_phone_number_id', '')
        self.access_token = access_token or getattr(config, 'whatsapp_access_token', '')
        self.verify_token = verify_token or getattr(config, 'whatsapp_verify_token', '')
    
    @property
    def channel_name(self) -> str:
        return "whatsapp_cloud"
    
    async def verify_webhook(self, payload: Dict[str, Any]) -> bool:
        """Verifica el token de webhook de WhatsApp."""
        mode = payload.get("hub.mode")
        token = payload.get("hub.verify_token")
        challenge = payload.get("hub.challenge")
        
        if mode == "subscribe" and token == self.verify_token:
            return True
        return False
    
    async def receive_message(self, payload: Dict[str, Any]) -> Message:
        """Parsea webhook de WhatsApp Cloud API."""
        entry = payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])
        
        if not changes:
            raise ValueError("No changes found in webhook payload")
        
        change = changes[0]
        value = change.get("value", {})
        
        # Verificar si es un mensaje
        messages = value.get("messages", [])
        if not messages:
            raise ValueError("No messages in webhook payload")
        
        message = messages[0]
        sender_id = message.get("from", "")
        
        # Determinar tipo de contenido
        msg_type = message.get("type", "text")
        content_type = self._map_content_type(msg_type)
        content = self._extract_content(message, msg_type)
        
        # Obtener información del contacto
        contacts = value.get("contacts", [{}])
        sender_name = None
        if contacts:
            profile = contacts[0].get("profile", {})
            sender_name = profile.get("name")
        
        return Message(
            channel=self.channel_name,
            external_id=message.get("id", ""),
            sender_id=sender_id,
            sender_name=sender_name,
            content_type=content_type,
            content=content,
            timestamp=float(message.get("timestamp", 0)),
            metadata={
                "wa_id": sender_id,
                "business_account_id": value.get("metadata", {}).get("phone_number_id", ""),
                "message_timestamp": message.get("timestamp")
            }
        )
    
    def _map_content_type(self, wa_type: str) -> str:
        """Mapea tipos de WhatsApp a tipos estándar."""
        mapping = {
            "text": "text",
            "image": "image",
            "audio": "audio",
            "voice": "audio",
            "video": "video",
            "document": "document",
            "sticker": "image",
            "location": "location",
            "contacts": "contacts"
        }
        return mapping.get(wa_type, "text")
    
    def _extract_content(self, message: dict, msg_type: str) -> Union[str, Dict[str, Any]]:
        """Extrae el contenido del mensaje según el tipo."""
        if msg_type == "text":
            return message.get("text", {}).get("body", "")
        elif msg_type in ["image", "audio", "video", "document"]:
            media_obj = message.get(msg_type, {})
            return {
                "id": media_obj.get("id"),
                "mime_type": media_obj.get("mime_type"),
                "caption": media_obj.get("caption"),
                "filename": media_obj.get("filename")
            }
        elif msg_type == "interactive":
            # Botones o listas
            interactive_obj = message.get("interactive", {})
            return {
                "type": interactive_obj.get("type"),
                "button_reply": interactive_obj.get("button_reply", {}),
                "list_reply": interactive_obj.get("list_reply", {})
            }
        return str(message)
    
    async def send_text(
        self, 
        recipient_id: str, 
        text: str, 
        reply_to: Optional[str] = None
    ) -> ChannelResponse:
        """Envía mensaje de texto."""
        if not self.access_token or not self.phone_number_id:
            return ChannelResponse(
                success=False,
                error="WhatsApp credentials not configured"
            )
        
        payload = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {"body": text}
        }
        
        if reply_to:
            payload["context"] = {"message_id": reply_to}
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                messages = data.get("messages", [])
                msg_id = messages[0].get("id") if messages else None
                
                return ChannelResponse(
                    success=True,
                    message_id=msg_id,
                    data=data
                )
        except Exception as e:
            logger.error(f"Error sending WhatsApp text: {e}")
            return ChannelResponse(success=False, error=str(e))
    
    async def send_media(
        self, 
        recipient_id: str, 
        media_type: str, 
        media_url_or_path: str, 
        caption: Optional[str] = None
    ) -> ChannelResponse:
        """Envía imagen/audio/video/documento."""
        if not self.access_token or not self.phone_number_id:
            return ChannelResponse(
                success=False,
                error="WhatsApp credentials not configured"
            )
        
        media_map = {
            "image": "image",
            "audio": "audio",
            "video": "video",
            "document": "document"
        }
        
        wa_type = media_map.get(media_type, "document")
        
        # Determinar si es URL o upload
        if media_url_or_path.startswith("http"):
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_id,
                "type": wa_type,
                wa_type: {"link": media_url_or_path}
            }
            if caption:
                payload[wa_type]["caption"] = caption
        else:
            # Upload de archivo local
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    with open(media_url_or_path, "rb") as f:
                        upload_resp = await client.post(
                            f"{self.base_url}/{self.phone_number_id}/media",
                            headers={"Authorization": f"Bearer {self.access_token}"},
                            files={"file": f},
                            data={
                                "messaging_product": "whatsapp",
                                "type": wa_type
                            }
                        )
                    upload_resp.raise_for_status()
                    media_id = upload_resp.json().get("id")
                    
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": recipient_id,
                        "type": wa_type,
                        wa_type: {"id": media_id}
                    }
                    if caption:
                        payload[wa_type]["caption"] = caption
            except Exception as e:
                return ChannelResponse(success=False, error=f"Upload failed: {e}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                response.raise_for_status()
                data = response.json()
                
                messages = data.get("messages", [])
                msg_id = messages[0].get("id") if messages else None
                
                return ChannelResponse(
                    success=True,
                    message_id=msg_id,
                    data=data
                )
        except Exception as e:
            logger.error(f"Error sending WhatsApp media: {e}")
            return ChannelResponse(success=False, error=str(e))
    
    async def send_audio_note(
        self, 
        recipient_id: str, 
        audio_file_path: str
    ) -> ChannelResponse:
        """Envía nota de voz (requiere formato OGG/OPUS)."""
        if not self.access_token or not self.phone_number_id:
            return ChannelResponse(
                success=False,
                error="WhatsApp credentials not configured"
            )
        
        try:
            # 1. Subir audio a Meta
            async with httpx.AsyncClient(timeout=60.0) as client:
                with open(audio_file_path, "rb") as f:
                    upload_resp = await client.post(
                        f"{self.base_url}/{self.phone_number_id}/media",
                        headers={"Authorization": f"Bearer {self.access_token}"},
                        files={"file": f},
                        data={
                            "messaging_product": "whatsapp",
                            "type": "audio"
                        }
                    )
                upload_resp.raise_for_status()
                media_id = upload_resp.json()["id"]
            
            # 2. Enviar mensaje referenciando el media_id
            async with httpx.AsyncClient(timeout=30.0) as client:
                send_resp = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": recipient_id,
                        "type": "audio",
                        "audio": {"id": media_id}
                    }
                )
                send_resp.raise_for_status()
                data = send_resp.json()
                
                messages = data.get("messages", [])
                msg_id = messages[0].get("id") if messages else None
                
                return ChannelResponse(
                    success=True,
                    message_id=msg_id,
                    data=data
                )
        except Exception as e:
            logger.error(f"Error sending WhatsApp voice note: {e}")
            return ChannelResponse(success=False, error=str(e))
    
    async def send_typing_indicator(
        self, 
        recipient_id: str, 
        is_typing: bool
    ) -> bool:
        """Muestra indicador de 'escribiendo...'."""
        if not self.access_token or not self.phone_number_id:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "to": recipient_id,
                        "type": "presence",
                        "presence": {"typing": is_typing}
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
        """Marca mensaje como leído."""
        if not self.access_token or not self.phone_number_id:
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/{self.phone_number_id}/messages",
                    headers={
                        "Authorization": f"Bearer {self.access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "messaging_product": "whatsapp",
                        "status": "read",
                        "message_id": message_id
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Error marking message as read: {e}")
            return False