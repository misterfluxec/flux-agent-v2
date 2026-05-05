"""
MÓDULO TTS - Edge-TTS con Caché-First + Circuit Breaker
========================================================
Arquitectura:
  1. Siempre buscar en caché primero (48h TTL)
  2. Si no existe, llamar a Edge-TTS con streaming por frases
  3. Si falla (403/timeout >3s), fallback a texto
  4. Circuit breaker: 3 reintentos con backoff, luego abrir circuito 5 min
"""

import io
import base64
import os
import hashlib
import logging
import asyncio
import time
from typing import Optional, List, AsyncGenerator
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()


class CircuitBreaker:
    """
    Circuit Breaker para APIs externas con estado persistente en Redis.
    Estados: CLOSED (normal), OPEN (bloqueado), HALF_OPEN (probando)
    """
    
    def __init__(self, max_retries: int = 3, timeout: float = 3.0, reset_timeout: int = 300):
        self.max_retries = max_retries
        self.timeout = timeout
        self.reset_timeout = reset_timeout
        self.cb_key = "tts:circuit_breaker"
        self.fails_key = f"{self.cb_key}:fails"
        self.opened_key = f"{self.cb_key}:opened_at"
        self.redis_client = None
    
    async def _get_redis(self):
        if self.redis_client is None:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(config.redis_url, decode_responses=False)
            except Exception as e:
                logger.warning(f"Redis no disponible para circuit breaker: {e}")
                return None
        return self.redis_client
    
    async def is_circuit_open(self) -> bool:
        """Verificar si el circuito está abierto (bloqueado)."""
        redis = await self._get_redis()
        if not redis:
            return False  # Si no hay Redis, permitir
        
        try:
            state = await redis.get(self.cb_key)
            state = state.decode('utf-8') if state else "CLOSED"
            
            if state == "OPEN":
                # Verificar si ya pasó el timeout
                opened_at = await redis.get(self.opened_key)
                if opened_at:
                    opened_ts = float(opened_at.decode('utf-8') if isinstance(opened_at, bytes) else opened_at)
                    if time.time() - opened_ts > self.reset_timeout:
                        # Cambiar a HALF_OPEN para probar
                        await redis.set(self.cb_key, "HALF_OPEN")
                        logger.info("Circuit breaker: Cambiando a HALF_OPEN (prueba)")
                        return False
                return True
            
            return state == "HALF_OPEN"  # En HALF_OPEN también permitir intentos
            
        except Exception as e:
            logger.warning(f"Error verificando circuit breaker: {e}")
            return False
    
    async def record_success(self):
        """Registrar éxito - cerrar circuito."""
        redis = await self._get_redis()
        if redis:
            try:
                await redis.set(self.cb_key, "CLOSED")
                await redis.set(self.fails_key, "0")
                logger.debug("Circuit breaker: Cerrado (success)")
            except Exception as e:
                logger.warning(f"Error guardando success: {e}")
    
    async def record_failure(self):
        """Registrar fallo - abrir circuito si supera threshold."""
        redis = await self._get_redis()
        if not redis:
            return
        
        try:
            fails = await redis.incr(self.fails_key)
            fails = int(fails)
            
            logger.warning(f"Circuit breaker: Fallo #{fails}/{self.max_retries}")
            
            if fails >= self.max_retries:
                await redis.set(self.cb_key, "OPEN")
                await redis.set(self.opened_key, str(time.time()))
                await redis.expire(self.fails_key, 3600)  # Reset fails en 1h
                logger.error("Circuit breaker: ABIERTO tras 3 fallos consecutivos")
        except Exception as e:
            logger.warning(f"Error guardando failure: {e}")
    
    async def call(self, func, *args, **kwargs):
        """Ejecutar función con circuit breaker y Redis."""
        # Verificar si el circuito está abierto
        if await self.is_circuit_open():
            raise Exception("Circuit breaker OPEN - saltando a fallback")
        
        last_error = None
        for attempt in range(self.max_retries):
            try:
                result = await func(*args, **kwargs)
                await self.record_success()
                return result
            except Exception as e:
                last_error = e
                delay = (2 ** attempt) * 0.5  # Backoff exponencial
                logger.warning(f"Intento {attempt + 1}/{self.max_retries} falló: {e}. Reintentando en {delay}s...")
                await asyncio.sleep(delay)
        
        # Si todos los intentos fallan
        await self.record_failure()
        raise last_error or Exception("TTS falló después de reintentos")


class TTSCacheManager:
    """Gestor de caché para TTS - Redis + Disco local."""
    
    def __init__(self):
        self.cache_dir = config.tts_cache_dir
        self.ttl = config.tts_cache_ttl
        self.max_size_bytes = int(config.tts_cache_max_size_gb * 1024 * 1024 * 1024)
        self.redis_client = None
        self._init_cache_dir()
    
    def _init_cache_dir(self):
        """Inicializar directorio de caché."""
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Cache TTS inicializado: {self.cache_dir}")
    
    async def _get_redis(self):
        """Obtener cliente Redis de forma lazy."""
        if self.redis_client is None:
            try:
                import redis.asyncio as redis
                self.redis_client = redis.from_url(config.redis_url, decode_responses=False)
            except Exception as e:
                logger.warning(f"Redis no disponible para caché: {e}")
                return None
        return self.redis_client
    
    def _get_cache_key(self, text: str) -> str:
        """Generar clave de caché desde el texto."""
        return f"tts:{hashlib.md5(text.encode('utf-8')).hexdigest()}"
    
    async def get(self, text: str) -> Optional[bytes]:
        """Obtener audio del caché (CACHE-FIRST)."""
        cache_key = self._get_cache_key(text)
        
        # 1. Buscar en Redis índice
        redis = await self._get_redis()
        if redis:
            try:
                index_data = await redis.get(f"idx:{cache_key}")
                if index_data:
                    file_path = index_data.decode('utf-8') if isinstance(index_data, bytes) else index_data
                    if os.path.exists(file_path):
                        async with aiofiles.open(file_path, 'rb') as f:
                            audio_data = await f.read()
                        await redis.expire(f"idx:{cache_key}", self.ttl)
                        logger.info(f"Cache HIT (Redis): {cache_key[:16]}...")
                        return audio_data
            except Exception as e:
                logger.warning(f"Error leyendo de Redis: {e}")
        
        # Fallback: buscar en disco
        file_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        if os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    audio_data = await f.read()
                logger.info(f"Cache HIT (disco): {cache_key[:16]}...")
                return audio_data
            except Exception as e:
                logger.error(f"Error leyendo archivo de caché: {e}")
        
        return None
    
    async def set(self, text: str, audio_data: bytes) -> bool:
        """Guardar audio en caché."""
        cache_key = self._get_cache_key(text)
        file_path = os.path.join(self.cache_dir, f"{cache_key}.mp3")
        
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(audio_data)
            
            await self._enforce_max_size()
            
            redis = await self._get_redis()
            if redis:
                try:
                    await redis.setex(f"idx:{cache_key}", self.ttl, file_path)
                except Exception as e:
                    logger.warning(f"Error guardando índice en Redis: {e}")
            
            logger.info(f"Cache WRITE: {cache_key[:16]}... ({len(audio_data)} bytes)")
            return True
        except Exception as e:
            logger.error(f"Error guardando en caché: {e}")
            return False
    
    async def _enforce_max_size(self):
        """Política LRU: eliminar archivos antiguos si se supera el tamaño máximo."""
        try:
            total_size = 0
            files = []
            
            for entry in os.scandir(self.cache_dir):
                if entry.is_file() and entry.name.endswith('.mp3'):
                    stat = entry.stat()
                    total_size += stat.st_size
                    files.append((entry.path, stat.st_mtime))
            
            if total_size > self.max_size_bytes:
                files.sort(key=lambda x: x[1])
                target_size = int(self.max_size_bytes * 0.8)
                
                for file_path, _ in files:
                    if total_size <= target_size:
                        break
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        total_size -= file_size
                        logger.info(f"Cache LRU eliminado: {os.path.basename(file_path)[:16]}...")
                    except Exception as e:
                        logger.error(f"Error eliminando archivo: {e}")
        except Exception as e:
            logger.error(f"Error en política LRU: {e}")


class EdgeTTSCapability:
    """
    TTS con Cache-First + Streaming por Frases + Circuit Breaker.
    """
    
    def __init__(self):
        self.voice = config.tts_voice
        self.cache_manager = TTSCacheManager() if config.tts_cache_enabled else None
        self.circuit_breaker = CircuitBreaker(max_retries=3, timeout=3.0, reset_timeout=300)
    
    async def _call_edge_tts(self, text: str) -> bytes:
        """Llamar a Edge-TTS con manejo de errores."""
        import edge_tts
        from edge_tts import Communicate
        
        communicate = Communicate(text, self.voice)
        audio_chunks = []
        
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_chunks.append(chunk["data"])
        
        return b"".join(audio_chunks)
    
    async def synthesize(self, text: str) -> str:
        """
        Síntesis con CACHE-FIRST + Circuit Breaker.
        Retorna audio en base64.
        """
        if not text or not text.strip():
            return ""
        
        # 1. CACHE-FIRST: Verificar caché
        if self.cache_manager:
            cached_audio = await self.cache_manager.get(text)
            if cached_audio:
                return base64.b64encode(cached_audio).decode("utf-8")
        
        # 2. Intentar Edge-TTS con Circuit Breaker
        try:
            audio_bytes = await self.circuit_breaker.call(self._call_edge_tts, text.strip())
            
            if audio_bytes and len(audio_bytes) > 0:
                # 3. Guardar en caché
                if self.cache_manager:
                    await self.cache_manager.set(text, audio_bytes)
                
                return base64.b64encode(audio_bytes).decode("utf-8")
            
            raise Exception("Edge-TTS retornó audio vacío")
            
        except Exception as e:
            logger.error(f"Edge TTS falló (circuit open o timeout): {e}")
            # 4. Fallback: pyttsx3 (offline, sin internet)
            try:
                import pyttsx3
                engine = pyttsx3.init()
                for voice in engine.getProperty('voices'):
                    if 'spanish' in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                engine.setProperty('rate', 150)
                import uuid
                tmp_file = f"/tmp/tts_{uuid.uuid4().hex[:8]}.wav"
                engine.save_to_file(text, tmp_file)
                engine.runAndWait()
                with open(tmp_file, 'rb') as f:
                    audio_bytes = f.read()
                os.remove(tmp_file)
                if audio_bytes and len(audio_bytes) > 0:
                    if self.cache_manager:
                        await self.cache_manager.set(text, audio_bytes)
                    return base64.b64encode(audio_bytes).decode("utf-8")
            except Exception as pyttsx_err:
                logger.error(f"pyttsx3 fallback falló: {pyttsx_err}")
            
            # 5. Fallback final: retornar string vacío
            return ""
    
    async def synthesize_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """
        Streaming no bloqueante por frases.
        No usa caché para streaming (el áudio se envía mientras se genera).
        """
        if not text or not text.strip():
            return
        
        # Dividir en frases
        phrases = text.replace(". ", ".|").replace("! ", "!|").replace("? ", "?|").split("|")
        
        try:
            import edge_tts
            from edge_tts import Communicate
            
            for phrase in phrases:
                if not phrase.strip():
                    continue
                
                communicate = Communicate(phrase.strip(), self.voice)
                
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        yield chunk["data"]
                    
                # Breve pausa entre frases para evitar saturación
                await asyncio.sleep(0.05)
                
        except Exception as e:
            logger.error(f"Error en synthesize_stream: {e}")
            yield b""
    
    async def synthesize_to_fallback(self, text: str) -> dict:
        """
        Síntesis completa con fallback a texto.
        Retorna dict con {'audio': base64, 'is_fallback': bool, 'text': str}
        """
        audio = await self.synthesize(text)
        
        if audio:
            return {"audio": audio, "is_fallback": False, "text": ""}
        
        # Fallback a texto
        return {"audio": "", "is_fallback": True, "text": text}


class CapabilityRegistry:
    """Registro singleton de capacidades TTS."""
    _instances = {}
    
    @classmethod
    def get_tts(cls) -> EdgeTTSCapability:
        if "tts" not in cls._instances:
            cls._instances["tts"] = EdgeTTSCapability()
        return cls._instances["tts"]
    
    @classmethod
    def get_cache_stats(cls) -> dict:
        if "tts" in cls._instances:
            return cls._instances["tts"].cache_manager.get_stats()
        return {}


async def synthesize_text(text: str) -> str:
    """Función principal de síntesis."""
    tts = CapabilityRegistry.get_tts()
    return await tts.synthesize(text)


async def synthesize_with_fallback(text: str) -> dict:
    """Síntesis con fallback a texto."""
    tts = CapabilityRegistry.get_tts()
    return await tts.synthesize_to_fallback(text)


class PiperTTSCapability:
    """Fallback a Piper TTS (local, sin internet)."""
    
    @staticmethod
    async def synthesize(text: str) -> str:
        """Síntesis con Piper - solo si está disponible el modelo."""
        piper_model = os.getenv("PIPER_MODEL_PATH", "/app/models/es_MX-david-medium.onnx")
        
        if not os.path.exists(piper_model):
            logger.warning(f"Modelo Piper no encontrado: {piper_model}")
            return ""
        
        try:
            from piper import PiperVoice
            voice = PiperVoice.load(piper_model)
            
            audio_buffer = io.BytesIO()
            voice.synthesize(text, audio_buffer)
            audio_buffer.seek(0)
            audio_bytes = audio_buffer.read()
            
            return base64.b64encode(audio_bytes).decode("utf-8")
            
        except Exception as e:
            logger.error(f"Error en Piper TTS: {e}")
            return ""
    
    @staticmethod
    async def synthesize_chunked(text: str) -> list:
        return []