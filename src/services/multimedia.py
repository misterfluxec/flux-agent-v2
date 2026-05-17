import base64
import os
import tempfile
import logging
import httpx
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

# -----------------------------------------------------------------------------
# LAZY LOAD MODELS
# -----------------------------------------------------------------------------
_whisper_model = None
def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            from faster_whisper import WhisperModel
            logger.info("Cargando model Faster-Whisper (base, int8, 4 threads)...")
            # compute_type="int8" to minimize RAM/VRAM
            # cpu_threads=4 to avoid maxing out the i7
            _whisper_model = WhisperModel("base", device="cpu", compute_type="int8", cpu_threads=4)
            logger.info("Modelo Faster-Whisper cargado exitosamente.")
        except ImportError:
            logger.error("faster-whisper no está instalado. STT fallará.")
            raise
    return _whisper_model

class ServicioMultimedia:
    @staticmethod
    async def transcribir_audio(b64_audio: str) -> str:
        """
        Transcribe un archivo de audio codificado en Base64 a texto.
        """
        try:
            audio_bytes = base64.b64decode(b64_audio)
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as tmp_file:
                tmp_file.write(audio_bytes)
                tmp_file_path = tmp_file.name

            try:
                model = get_whisper_model()
                logger.info(f"Transcribiendo audio {tmp_file_path}...")
                segments, info = model.transcribe(tmp_file_path, beam_size=5)
                texto_transcrito = " ".join([segment.text for segment in segments])
                logger.info(f"Transcripción exitosa: {texto_transcrito[:50]}...")
                return texto_transcrito.strip()
            finally:
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        except Exception as e:
            logger.error(f"Error transcribiendo audio: {e}")
            return ""

    @staticmethod
    async def sintetizar_voz(texto: str) -> str:
        """
        Sintetiza texto a voz usando Edge TTS (primero) o Piper (fallback).
        Retorna Base64 del audio MP3/WAV.
        """
        try:
            from core.capabilities.tts import synthesize_text
            return await synthesize_text(texto)
        except Exception as e:
            logger.error(f"Error en sintetizar_voz: {e}")
            return ""

    @staticmethod
    async def analizar_imagen(b64_image: str, prompt: str = "Describe esta imagen detalladamente para un asistente de ventas.") -> str:
        """
        Envía una imagen Base64 al model Moondream en Ollama y devuelve la descripción.
        Optimizado para CPU i7 (Moondream es ~1.4B parameters).
        """
        logger.info("Analizando imagen con moondream (Ollama)...")
        try:
            # Usamos httpx directo hacia Ollama
            async with httpx.AsyncClient(timeout=120.0) as client:
                payload = {
                    "model": "moondream",
                    "keep_alive": "5m",
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt,
                            "images": [b64_image]
                        }
                    ],
                    "stream": False
                }
                resp = await client.post(f"{config.ollama_base_url}/api/chat", json=payload)
                resp.raise_for_status()
                data = resp.json()
                description = data.get("message", {}).get("content", "")
                logger.info(f"Imagen analizada: {description[:50]}...")
                return description.strip()
        except Exception as e:
            logger.error(f"Error analizando imagen: {e}")
            return ""
