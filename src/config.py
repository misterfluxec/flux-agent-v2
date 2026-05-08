# =============================================================================
# FLUXAGENT V2 — CONFIGURACIÓN CENTRALIZADA
# =============================================================================
# Todos los parámetros de configuración se leen desde variables de entorno.
# Nunca se deben hardcodear secretos en el código.
# =============================================================================

import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Configuracion(BaseSettings):
    """
    Configuración global de la aplicación.
    Se carga desde variables de entorno o archivo .env
    """

    model_config = SettingsConfigDict(
        env_file=[".env", "../.env"],
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Información de la Aplicación
    # -------------------------------------------------------------------------
    app_nombre: str = "FluxAgent V2"
    app_version: str = "2.0.0"
    app_env: str = "development"      # development | staging | production
    log_level: str = "INFO"

    # -------------------------------------------------------------------------
    # Base de Datos
    # -------------------------------------------------------------------------
    database_url: str = "postgresql://fluxadmin:fluxsecure2026@localhost:5434/fluxagent_v2"
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_pool_pre_ping: bool = True     # Verifica la conexión antes de usarla

    # -------------------------------------------------------------------------
    # Redis & Event Bus
    # -------------------------------------------------------------------------
    redis_url: str = "redis://:redisflux2026@localhost:6381/0"
    event_stream_maxlen: int = 100000
    max_event_retries: int = 3
    event_processing_timeout: int = 30
    tool_rate_limit: int = 100
    
    # -------------------------------------------------------------------------
    # Ollama (LLM Engine)
    # -------------------------------------------------------------------------
    @property
    def ollama_base_url(self) -> str:
        """URL dinámica de Ollama basada en entorno o configuración."""
        # Prioridad: variable de entorno > docker network > localhost
        external_url = os.getenv("OLLAMA_BASE_URL")
        if external_url:
            return external_url
        
        # Para Docker Compose: usar nombre del contenedor
        if os.getenv("APP_ENV") == "production":
            return "http://ollama:11434"
        
        # Para desarrollo local
        return "http://localhost:11434"
    
    ollama_modelo_chat: str = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:3b")
    ollama_modelo_embedding: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    ollama_timeout: int = int(os.getenv("OLLAMA_TIMEOUT", "120"))
    ollama_max_loaded_models: int = int(os.getenv("OLLAMA_MAX_LOADED", "3"))

    # -------------------------------------------------------------------------
    # Autenticación JWT
    # -------------------------------------------------------------------------
    jwt_secret: str = "cambiar_en_produccion_jwt_secret"
    jwt_algoritmo: str = "HS256"
    jwt_expire_minutos: int = 60

    # -------------------------------------------------------------------------
    # CORS
    # -------------------------------------------------------------------------
    cors_origins: List[str] = [
        "http://localhost:4000", 
        "http://localhost:3000",
        "https://app.labodegaec.com",
        "https://api.labodegaec.com"
    ]

    # -------------------------------------------------------------------------
    # Subida de Archivos
    # -------------------------------------------------------------------------
    uploads_dir: str = "/app/uploads"
    max_file_size_mb: int = 50
    tipos_permitidos: List[str] = ["pdf", "xlsx", "xls", "csv", "txt"]

    # -------------------------------------------------------------------------
    # Embeddings (dimensión del vector)
    # -------------------------------------------------------------------------
    embedding_dimension: int = 768    # nomic-embed-text via Ollama (verificado en producción)

    # -------------------------------------------------------------------------
    # Evolution API (WhatsApp)
    # -------------------------------------------------------------------------
    evolution_api_url: str = "http://flux-evolution:8080"
    evolution_api_key: str = "fluxkey123"

    # -------------------------------------------------------------------------
    # LLM Cloud Providers (desactivados por defecto)
    # -------------------------------------------------------------------------
    llm_mode: str = "local"           # local | cloud
    default_cloud_provider: str = "openai"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""

    # -------------------------------------------------------------------------
    # TTS Cache (Edge-TTS con caché local)
    # -------------------------------------------------------------------------
    tts_cache_enabled: bool = True    # Habilitar/deshabilitar caché
    tts_cache_dir: str = "/app/data/media/tts_cache"  # Directorio de caché
    tts_cache_ttl: int = 172800        # TTL: 48 horas en segundos
    tts_cache_max_size_gb: float = 2.0  # Máximo tamaño del directorio
    tts_voice: str = "es-MX-DaliaNeural"  # Voz por defecto

    # -------------------------------------------------------------------------
    # Canales de Mensajería
    # -------------------------------------------------------------------------
    # WhatsApp Cloud API
    whatsapp_phone_number_id: str = ""
    whatsapp_access_token: str = ""
    whatsapp_verify_token: str = "whatsapp_verify_token"
    
    # Telegram Bot
    telegram_bot_token: str = ""

    @property
    def es_produccion(self) -> bool:
        """Retorna True si el entorno es producción."""
        return self.app_env == "production"

    @property
    def es_desarrollo(self) -> bool:
        """Retorna True si el entorno es desarrollo."""
        return self.app_env == "development"


@lru_cache
def obtener_config() -> Configuracion:
    """
    Retorna la instancia de configuración (singleton con caché).
    Usar con FastAPI Depends: config = Depends(obtener_config)
    """
    return Configuracion()
