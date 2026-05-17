import os
import logging
from typing import AsyncGenerator, Optional

# Imports condicionales para Pipecat (solo si está instalado)
try:
    from pipecat.pipeline.pipeline import Pipeline
    from pipecat.pipeline.task import PipelineTask
    from pipecat.pipeline.runner import PipelineRunner
    from pipecat.transports.websocket.fastapi import FastAPIWebsocketTransport, FastAPIWebsocketParams
    from pipecat.serializers.base_serializer import FrameSerializer
    from pipecat.frames.frames import EndFrame, Frame, InputAudioRawFrame, OutputAudioRawFrame
    from pipecat.audio.vad.silero import SileroVADAnalyzer
    from pipecat.processors.aggregators.llm_response_universal import LLMContextAggregatorPair, LLMUserAggregatorParams
    from pipecat.processors.aggregators.llm_response_universal import LLMContext # Fallback import
    from pipecat.services.whisper.stt import WhisperSTTService
    from pipecat.services.ollama.llm import OLLamaLLMService
    from pipecat.services.piper.tts import PiperTTSService
    import json
    # Removed OpenAI import to avoid websockets.asyncio missing error on startup
    PIPECAT_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import Pipecat dependencies: {e}")
    PIPECAT_AVAILABLE = False
    Pipeline = None  # Definir Pipeline como None si no está disponible
    FrameSerializer = None  # Definir FrameSerializer como None si está disponible
    Frame = None  # Definir Frame como None si no está disponible
    OutputAudioRawFrame = None  # Definir OutputAudioRawFrame como None si no está disponible
    import base64
    
    class JSONBase64Serializer:
        def __init__(self, sample_rate: int = 16000, channels: int = 1):
            self.sample_rate = sample_rate
            self.channels = channels

        async def serialize(self, frame):
            if hasattr(frame, 'audio'):  # Check if it has audio attribute
                data = base64.b64encode(frame.audio).decode("utf-8")
                return json.dumps({"type": "audio", "data": data})
            return None

        async def deserialize(self, data: str | bytes):
            logger.info(f"DEBUG: Raw data received in serializer: {type(data)} - len: {len(data)}")
            try:
                if isinstance(data, bytes):
                    data = data.decode("utf-8")
                msg = json.loads(data)
                if msg.get("type") == "audio" and msg.get("data"):
                    logger.info(f"DEBUG: Received audio frame of length {len(msg['data'])}")
                    audio_bytes = base64.b64decode(msg["data"])
                    return InputAudioRawFrame(audio=audio_bytes, sample_rate=self.sample_rate, num_channels=self.channels)
            except Exception as e:
                logger.error(f"ERROR deserializing frame: {e} - data: {data[:50]}")
            return None

    PIPECAT_AVAILABLE = True
except ImportError as e:
    print(f"Failed to import Pipecat dependencies: {e}")
    PIPECAT_AVAILABLE = False

logger = logging.getLogger(__name__)

class OpenSourceVoicePipeline:
    """Pipeline optimizado para CPU (i7 7th Gen)"""
    
    def __init__(self, websocket, tenant_config: dict):
        self.websocket = websocket
        self.tenant_config = tenant_config
        
        # Configuración optimizada para CPU
        self.sample_rate = 16000
        self.whisper_model = "tiny"  # CRÍTICO: no usar "base" o mayor en CPU limitada
        self.ollama_model = "qwen2.5:3b"
        self.ollama_base_url = tenant_config.get("ollama_url", "http://127.0.0.1:11434/v1")
        
        # Voz Piper: Priorizar es_MX para LATAM, fallback a es_ES
        self.piper_voice = self._select_piper_voice(tenant_config.get("locale", "es"))
    
    def _select_piper_voice(self, locale: str) -> str:
        """Selecciona voz Piper según language, con fallback seguro"""
        voice_map = {
            "es": "es_ES-davefx-medium",  # Disponible por defecto
            "es_MX": "es_MX-ald-medium",   # Verificar disponibilidad al inicio
            "en": "en_US-lessac-medium",
            "pt": "pt_BR-edresson-medium",
        }
        # Fallback a es_ES si la voz específica no está disponible
        return voice_map.get(locale, voice_map["es"])
        
    async def _verify_piper_voice(self, voice: str) -> str:
        """Verifica si la voz está disponible; si no, usa fallback"""
        try:
            from piper import PiperVoice
            # Intentar cargar la voz; si falla, usar fallback
            PiperVoice.load(voice, model_dir="./models/piper")
            return voice
        except Exception:
            logger.warning(f"Voice {voice} not available, falling back to es_ES-davefx-medium")
            return "es_ES-davefx-medium"
    
    async def create_pipeline(self) -> Pipeline:
        """Construye el pipeline con servicios optimizados"""
        # 1. Transporte WebSocket (FastAPI)
        transport = FastAPIWebsocketTransport(
            websocket=self.websocket,
            params=FastAPIWebsocketParams(
                audio_out_sample_rate=self.sample_rate,
                audio_out_channels=1,
                audio_in_enabled=True,
                audio_in_sample_rate=self.sample_rate,
                audio_in_channels=1,
                serializer=JSONBase64Serializer(sample_rate=self.sample_rate, channels=1)
            )
        )
        
        # 2. VAD (Silero - CPU efficient, parámetros reducidos para más sensibilidad)
        vad_analyzer = SileroVADAnalyzer(
            sample_rate=self.sample_rate,
        )
        context = LLMContext()
        user_aggregator, assistant_aggregator = LLMContextAggregatorPair(
            context,
            user_params=LLMUserAggregatorParams(
                vad_analyzer=vad_analyzer,
            ),
        )
        
        # 3. STT (Whisper tiny - optimizado para CPU)
        stt = WhisperSTTService(
            model=self.whisper_model,
            # No device passed unless supported, but default is often cpu
        )
        
        # 4. LLM (Ollama con parámetros optimizados)
        llm = OLLamaLLMService(
            model=self.ollama_model,
            base_url=self.ollama_base_url,
            # Parámetros para baja latencia en CPU:
            options={
                "num_predict": 128,  # Limitar longitud de respuesta
                "temperature": 0.7,
                "top_p": 0.9,
                "stop": ["\n\n", "Usuario:", "Humano:"]  # Evitar divagaciones
            }
        )
        
        # 5. TTS (Piper con voz seleccionada)
        import pathlib
        tts = PiperTTSService(
            voice_id=await self._verify_piper_voice(self.piper_voice),
            download_dir=pathlib.Path("./models/piper"),
            # Optimizaciones para CPU
        )
        
        # 6. Construir pipeline (sort_order crítico)
        pipeline = Pipeline([
            transport.input(),      # Audio entrante
            stt,                    # Voz → Texto
            user_aggregator,        # Add user message to context con VAD
            llm,                    # Texto → Respuesta (cerebro)
            tts,                    # Texto → Voz
            transport.output(),     # Audio saliente
            assistant_aggregator,   # Add bot response to context
        ])
        
        return pipeline
    
    async def run(self):
        """Ejecuta el pipeline con manejo de errores robusto"""
        try:
            pipeline = await self.create_pipeline()
            # idle_timeout_secs=None → pipeline runs indefinitely until transport disconnects
            task = PipelineTask(pipeline, idle_timeout_secs=None)
            runner = PipelineRunner()
            
            # Iniciar runner (bloqueará hasta que el transport reciba EndFrame o se desconecte)
            logger.info("🚀 Iniciando PipelineTask...")
            await runner.run(task)
            logger.info("🏁 PipelineTask finalizado.")
            
        except Exception as e:
            logger.error(f"Voice pipeline error: {e}", exc_info=True)
            # Enviar error al frontend para feedback al usuario
            try:
                await self.websocket.send_json({"type": "error", "message": "Error procesando voz"})
            except:
                pass
        finally:
            try:
                await self.websocket.close()
            except:
                pass

class VoicePipelineService:
    def __init__(self, tenant_config: dict):
        self.tenant_config = tenant_config
        self.is_premium = tenant_config.get("is_premium", False)
        self.api_key = os.getenv("OPENAI_API_KEY")
        
    async def create_pipeline(self, websocket):
        if not PIPECAT_AVAILABLE:
            raise Exception("Pipecat no está instalado.")

        if self.is_premium:
            transport = FastAPIWebsocketTransport(
                websocket=websocket,
                params=FastAPIWebsocketParams(
                    audio_out_sample_rate=16000,
                    audio_out_channels=1,
                    audio_in_enabled=True,
                    audio_in_sample_rate=16000,
                    audio_in_channels=1,
                    serializer=JSONBase64Serializer()
                )
            )
            from pipecat.services.openai.realtime.llm import OpenAIRealtimeLLMService
            service = OpenAIRealtimeLLMService(
                api_key=self.api_key,
                # Pipecat 1.1 OpenAIRealtimeLLMService parameters
            )
            pipeline = Pipeline([transport.input(), service, transport.output()])
            return pipeline
        else:
            raise Exception("Use OpenSourceVoicePipeline directamente")

    async def process_audio_stream(self, websocket):
        if self.is_premium:
            pipeline = await self.create_pipeline(websocket)
            task = PipelineTask(pipeline)
            runner = PipelineRunner()
            await runner.run(task)
        else:
            os_pipeline = OpenSourceVoicePipeline(websocket, self.tenant_config)
            await os_pipeline.run()
