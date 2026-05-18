import logging
import logging.handlers
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from config import obtener_config
from core.middleware.registry import setup_middlewares
from core.routers.registry import register_routers
from core.lifecycle.infrastructure import initialize_infrastructure, cleanup_infrastructure
from core.observability.logging import StructuredLogHandler, StructuredLogFormatter
from core.metrics import start_metrics_server

# =============================================================================
# LOGGING SETUP
# =============================================================================
os.makedirs("logs", exist_ok=True)
_log_handler = StructuredLogHandler()
_log_handler.setFormatter(StructuredLogFormatter())
_log_handler.setLevel(logging.INFO)

_file_handler = logging.handlers.RotatingFileHandler("logs/fluxagent.log", maxBytes=10*1024*1024, backupCount=5)
_file_handler.setFormatter(StructuredLogFormatter())
_file_handler.setLevel(logging.INFO)

logging.root.handlers.clear()
logging.root.addHandler(_log_handler)
logging.root.addHandler(_file_handler)
logging.root.setLevel(logging.INFO)

for _noisy in ("uvicorn.access", "httpx", "httpcore"):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)
config = obtener_config()

# =============================================================================
# CICLO DE VIDA (LIFESPAN)
# =============================================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida limpio: solo infraestructura y orquestación."""
    logger.info(f"🚀 Iniciando {config.app_nombre} v{config.app_version} [{config.app_env}]")
    await initialize_infrastructure(app)
    
    # Iniciar servidor de métricas Prometheus
    try:
        start_metrics_server(8001)
        logger.info("📊 Métricas Prometheus disponibles en http://localhost:8001/metrics")
    except Exception as e:
        logger.warning(f"⚠️ Servidor métricas no iniciado: {e}")
        
    # Scheduler de recordatorios cada 30 min (Ecuador Local Time naive)
    import asyncio
    async def reminder_loop():
        # Esperar un momento en el arranque antes de disparar el primer check
        await asyncio.sleep(10)
        while True:
            try:
                from tasks.reminder_scheduler import check_and_schedule_reminders
                check_and_schedule_reminders.send()
                logger.info("⏰ Tarea check_and_schedule_reminders encolada en Dramatiq")
            except Exception as exc:
                logger.warning("reminder_scheduler_error", extra={"error": str(exc)})
            await asyncio.sleep(1800)  # 30 minutos

    asyncio.create_task(reminder_loop())

    yield
    logger.info("🛑 Cerrando aplicación...")
    await cleanup_infrastructure(app)

# =============================================================================
# APP FACTORY
# =============================================================================
def create_app() -> FastAPI:
    app = FastAPI(
        title=config.app_nombre,
        version=config.app_version,
        description="Motor de Agentes IA Multi-tenant con RAG y Streaming",
        lifespan=lifespan,
        docs_url="/docs" if config.es_desarrollo else None,
        redoc_url="/redoc" if config.es_desarrollo else None,
    )

    # Archivos estáticos
    os.makedirs("uploads/avatars", exist_ok=True)
    os.makedirs("uploads/knowledge", exist_ok=True)
    app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

    # Inyección de middlewares y rutas (state se inicializa en infrastructure.py)
    setup_middlewares(app)
    register_routers(app)
    
    logger.info("✅ Aplicación inicializada correctamente")
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=9000,
        reload=config.es_desarrollo,
        log_level=config.log_level.lower()
    )
