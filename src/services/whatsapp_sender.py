"""
WhatsApp Sender - Evolution API con efecto de streaming
========================================================
Envía notas de voz simulando "grabación en vivo" para naturalidad.
"""

import httpx
import base64
import logging
from typing import Optional
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

EVOLUTION_API_URL = config.evolution_api_url
API_KEY = config.evolution_api_key


async def send_presence_recording(instance_name: str, phone_number: str, delay: int = 1200):
    """
    Activa presencia 'recording' - muestra ondas de voz al cliente.
    """
    if not API_KEY:
        logger.warning("EVOLUTION_API_KEY no configurado")
        return
    
    headers = {"apikey": API_KEY}
    payload = {
        "number": phone_number.replace("+", ""),
        "delay": delay,
        "presence": "recording"
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{EVOLUTION_API_URL}/chat/sendPresence/{instance_name}",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            logger.info(f"Presence 'recording' sent to {phone_number}")
    except Exception as e:
        logger.warning(f"Error sending presence: {e}")


async def send_voice_note_with_streaming_effect(
    instance_name: str,
    phone_number: str,
    audio_base64: str,
    audio_mimetype: str = "audio/mp4",
    caption: Optional[str] = None
) -> bool:
    """
    Envía nota de voz con efecto 'grabación en vivo'.
    """
    if not API_KEY:
        logger.warning("EVOLUTION_API_KEY no configurado")
        return False
    
    headers = {"apikey": API_KEY}
    
    # Limpiar número
    clean_number = phone_number.replace("+", "").replace(" ", "")
    
    payload = {
        "number": clean_number,
        "mimetype": audio_mimetype,
        "audio": audio_base64,
        "delay": 800
    }
    
    if caption:
        payload["caption"] = caption
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{EVOLUTION_API_URL}/message/sendWhatsAppAudio/{instance_name}",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            logger.info(f"✅ Voice note sent to {phone_number}")
            return True
    except Exception as e:
        logger.error(f"❌ Error sending voice note to {phone_number}: {e}")
        return False


async def send_text_message(
    instance_name: str,
    phone_number: str,
    text: str
) -> bool:
    """
    Envía mensaje de texto.
    """
    if not API_KEY:
        return False
    
    headers = {"apikey": API_KEY}
    clean_number = phone_number.replace("+", "").replace(" ", "")
    
    payload = {
        "number": clean_number,
        "text": {"text": text}
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{EVOLUTION_API_URL}/message/sendText/{instance_name}",
                json=payload,
                headers=headers
            )
            resp.raise_for_status()
            logger.info(f"✅ Text sent to {phone_number}")
            return True
    except Exception as e:
        logger.error(f"Error sending text: {e}")
        return False


async def send_tts_with_fallback(
    instance_name: str,
    phone_number: str,
    text_response: str,
    audio_base64: str = ""
) -> dict:
    """
    Envía TTS con efecto streaming + fallback a texto.
    Retorna: {'success': bool, 'type': 'audio'|'text', 'message': str}
    """
    # 1. Si hay audio, intentar enviar con efecto recording
    if audio_base64:
        # Enviar presencia "recording" primero
        await send_presence_recording(instance_name, phone_number)
        
        # Enviar audio
        success = await send_voice_note_with_streaming_effect(
            instance_name, phone_number, audio_base64
        )
        
        if success:
            return {"success": True, "type": "audio", "message": "Voice note sent"}
    
    # 2. Fallback a texto
    fallback_text = f"🤖 {text_response}"
    if not audio_base64:
        fallback_text += "\n\n(Nota: Síntesis de voz temporalmente no disponible)"
    
    success = await send_text_message(instance_name, phone_number, fallback_text)
    
    return {
        "success": success,
        "type": "text",
        "message": "Fallback to text" if success else "Failed"
    }


async def send_whatsapp_message(
    instance_name: str,
    phone_number: str,
    text: str,
    audio_base64: str = ""
) -> dict:
    """
    Envío unificado de mensajes WhatsApp.
    Prioriza voz si está disponible, si no texto.
    """
    return await send_tts_with_fallback(instance_name, phone_number, text, audio_base64)


async def enviar_whatsapp_async(
    tenant_id: str,
    phone: str,
    message: str,
    media_url: Optional[str] = None,
    metadata: Optional[dict] = None
) -> dict:
    """
    Wrapper para async_tasks compatible con signature antigua.
    """
    instance_name = metadata.get("instance_name", f"instance_{tenant_id}") if metadata else f"instance_{tenant_id}"
    return await send_whatsapp_message(
        instance_name=instance_name,
        phone_number=phone,
        text=message,
        audio_base64="" # media_url not directly supported in base64 here
    )