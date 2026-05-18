import logging
from fastapi import FastAPI
from redis.asyncio import Redis, ConnectionPool
from config import obtener_config
from database import inicializar_db, cerrar_db
from core.encryption import EncryptionService
from core.resilience.distributed_lock import DistributedLockManager
from core.realtime_gateway import RealtimeGateway
from core.event_bus import EventBus
from core.ws_event_bridge import WSRealtimeBridge

logger = logging.getLogger(__name__)
config = obtener_config()

async def initialize_infrastructure(app: FastAPI):
    # 1. Cifrado
    try:
        EncryptionService.initialize()
    except Exception as e:
        logger.warning(f"⚠️ EncryptionService no iniciado: {e}")

    # 2. Base de datos
    await inicializar_db()

    # 3. Redis Pool Singleton
    redis_pool = ConnectionPool.from_url(
        config.redis_url,
        max_connections=25,
        socket_keepalive=True,
        health_check_interval=30,
        decode_responses=True,
    )
    app.state.redis = Redis(connection_pool=redis_pool)
    DistributedLockManager.set_redis(app.state.redis)

    try:
        await app.state.redis.ping()
        logger.info("✅ Redis conectado")
    except Exception as e:
        logger.warning(f"⚠️ Redis no disponible: {e}")

    # 4. EventBus & Realtime
    app.state.event_bus = EventBus(app.state.redis)
    app.state.realtime_gateway = RealtimeGateway(app.state.redis)
    ws_bridge = WSRealtimeBridge(app.state.realtime_gateway)
    ws_bridge.register(app.state.event_bus)

    # 4.5 Inyectar Orquestadores y Servicios en app.state
    from services.lead_scorer import LeadScorer
    from services.tool_executor import ToolExecutor
    from services.ai_memory import AIMemoryManager
    from services.policy_engine import PolicyEngine
    from services.ai_orchestrator import AIOrchestrator
    from services.usage_tracker import UsageTracker
    from services.quota_manager import QuotaManager
    from services.billing_alert_service import BillingAlertService

    app.state.lead_scorer = LeadScorer(app.state.redis, app.state.event_bus)
    app.state.lead_scorer.register()

    app.state.tool_executor = ToolExecutor()
    from core.tool_registry import COMMERCE_TOOLS
    for tool in COMMERCE_TOOLS:
        app.state.tool_executor.register(tool)

    app.state.memory_manager = AIMemoryManager(redis=app.state.redis, db_session=None)
    app.state.policy_engine = PolicyEngine(redis=app.state.redis, db=None)
    app.state.orchestrator = AIOrchestrator(
        redis=app.state.redis,
        event_bus=app.state.event_bus,
        policy_engine=app.state.policy_engine,
        tool_executor=app.state.tool_executor,
        memory_manager=app.state.memory_manager,
        llm_provider=None,
    )

    import asyncio
    from domain.events import EventType
    asyncio.create_task(
        app.state.event_bus.subscribe(
            event_types=[EventType.MESSAGE_RECEIVED, EventType.VOICE_TRANSCRIPTION_CHUNK],
            handler=app.state.orchestrator.process_event,
            consumer_name="ai-orchestrator",
        )
    )

    app.state.usage_tracker = UsageTracker(redis=app.state.redis, db_session_factory=None)
    app.state.quota_manager = QuotaManager(redis=app.state.redis, db_session_factory=None)
    await app.state.usage_tracker.start()

    app.state.billing_alert = BillingAlertService(app.state.event_bus, app.state.redis, None)

    # 5. Ollama Health Check
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{config.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                modelos = [m.get("name") for m in resp.json().get("models", [])]
                logger.info(f"✅ Ollama disponible. Modelos: {modelos}")
    except Exception as e:
        logger.warning(f"⚠️ Ollama no respondió: {e}")

    # 6. Iniciar Schedulers y Handlers (separados para limpieza)
    from core.lifecycle.events import register_event_handlers
    from core.lifecycle.schedulers import start_schedulers
    await register_event_handlers(app)
    await start_schedulers()

async def cleanup_infrastructure(app: FastAPI):
    try:
        from core.lifecycle.schedulers import stop_schedulers
        await stop_schedulers()
    except Exception: pass

    if hasattr(app.state, "usage_tracker"):
        await app.state.usage_tracker.stop()

    if hasattr(app.state, "event_bus"):
        await app.state.event_bus.close()
        
    if hasattr(app.state, "redis"):
        await app.state.redis.aclose()
        await cerrar_db()
        logger.info("🔴 Recursos liberados correctamente")
