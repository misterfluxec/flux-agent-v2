import os
from typing import AsyncGenerator, Optional

# Imports condicionales para Pipecat (solo si está instalado)
try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.services.openai import OpenAIRealtimeService
    from pipecat.transports.websocket import WebSocketTransport
    PIPECAT_AVAILABLE = True
except ImportError:
    PIPECAT_AVAILABLE = False

class VoicePipelineService:
    def __init__(self, tenant_config: dict):
        self.is_premium = tenant_config.get("is_premium", False)
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    async def create_pipeline(self, websocket):
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat no está instalado. Ejecuta: pip install pipecat-ai")

        if self.is_premium:
            # --- CONFIGURACIÓN PREMIUM (OpenAI Realtime) ---
            # Baja latencia, voces neuronales avanzadas
            transport = WebSocketTransport(websocket)
            
            # Configuración del servicio OpenAI Realtime
            service = OpenAIRealtimeService(
                api_key=self.api_key,
                model="gpt-4o-realtime-preview-2024-10-01",
                voice="alloy" # Opciones: alloy, echo, fable, onyx, nova, shimmer
            )
            
            pipeline = Pipeline([transport.input(), service, transport.output()])
            return pipeline
            
        else:
            # --- CONFIGURACIÓN STANDARD (Open Source / Local) ---
            # Usar Whisper local + TTS local (ej. Piper o Coqui)
            # Aquí iría la lógica con modelos locales para ahorrar costos
            # Por ahora, retornamos un mock o usamos una versión básica de OpenAI si es permitido
            raise NotImplementedError("El modo Open Source puro requiere configuración de modelos locales (Whisper/Piper).")

    async def process_audio_stream(self, websocket) -> AsyncGenerator[bytes, None]:
        # Lógica de streaming bidireccional
        pipeline = await self.create_pipeline(websocket)
        await pipeline.run()
