# =============================================================================
# FLUXAGENT V2 — APPLICATION LIFECYCLE
# =============================================================================

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from redis.asyncio import Redis, ConnectionPool

from config import obtener_config
from database import cerrar_db, inicializar_db
from core.metrics import start_metrics_server
from tasks.rag_scheduler import start_scheduler as start_rag_scheduler, stop_scheduler as stop_rag_scheduler

# Dependencies
from core.event_bus import EventBus
from core.ws_event_bridge import WSRealtimeBridge
from core.realtime_gateway import RealtimeGateway
from services.lead_scorer import LeadScorer
from services.tool_executor import ToolExecutor
from services.ai_memory import AIMemoryManager
from services.policy_engine import PolicyEngine
from services.ai_orchestrator import AIOrchestrator
from domain.events import EventType
from services.usage_tracker import UsageTracker
from services.quota_manager import QuotaManager

logger = logging.getLogger(__name__)
config = obtener_config()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Iniciando {config.app_nombre} v{config.app_version} [{config.app_env}]")

    # Inicializar servicio de cifrado (antes de cualquier operación con BD)
    try:
        from core.encryption import EncryptionService
        EncryptionService.initialize()
    except Exception as e:
        logger.warning(f"⚠️  EncryptionService no iniciado: {e}")

    await inicializar_db()

    # ─── REDIS POOL SINGLETON ───
    # Un solo ConnectionPool compartido para todo el ciclo de vida del servidor.
    redis_pool = ConnectionPool.from_url(
        config.redis_url,
        max_connections=20,
        socket_keepalive=True,
        socket_keepalive_options={},
        health_check_interval=30,
        decode_responses=True,
    )
    app.state.redis = Redis(connection_pool=redis_pool)
    redis_conn = app.state.redis

    # Wire distributed lock manager with real Redis
    from core.resilience.distributed_lock import DistributedLockManager
    DistributedLockManager.set_redis(redis_conn)
    logger.info("🔒 DistributedLockManager conectado a Redis")

    # Nuevo Gateway Unificado de Tiempo Real
    realtime_gateway = RealtimeGateway(redis_conn)
    app.state.realtime_gateway = realtime_gateway
    
    event_bus = EventBus(redis_conn)
    ws_bridge = WSRealtimeBridge(realtime_gateway)
    ws_bridge.register(event_bus)
    app.state.event_bus = event_bus

    # Registro de Telemetry Broadcaster (para TaskRunner)
    try:
        from core.tasks.dependencies import setup_telemetry_broadcaster
        setup_telemetry_broadcaster(app)
    except Exception as e:
        logger.warning(f"⚠️ Telemetry Broadcaster no iniciado: {e}")

    # Motor de Scoring
    lead_scorer = LeadScorer(redis_conn, event_bus)
    lead_scorer.register()
    app.state.lead_scorer = lead_scorer
    
    # Motor de Herramientas
    tool_executor = ToolExecutor() 
    from core.tool_registry import COMMERCE_TOOLS
    for tool in COMMERCE_TOOLS:
        tool_executor.register(tool)
    app.state.tool_executor = tool_executor

    # === NUEVO: AI Orchestrator + Policy Engine ===
    memory_manager = AIMemoryManager(redis=redis_conn, db_session=None)
    policy_engine = PolicyEngine(redis=redis_conn, db=None)
    
    orchestrator = AIOrchestrator(
        redis=redis_conn,
        event_bus=event_bus,
        policy_engine=policy_engine,
        tool_executor=tool_executor,
        memory_manager=memory_manager,
        llm_provider=None, # Inyectar provider real más adelante
    )
    
    # Suscribirse a eventos de entrada
    import asyncio
    asyncio.create_task(
        event_bus.subscribe(
            event_types=[EventType.MESSAGE_RECEIVED, EventType.VOICE_TRANSCRIPTION_CHUNK],
            handler=orchestrator.process_event,
            consumer_name="ai-orchestrator",
        )
    )
    
    # Guardar en app state para inyección en routers
    app.state.memory_manager = memory_manager
    app.state.orchestrator = orchestrator
    app.state.policy_engine = policy_engine

    # === NUEVO: Token Economy Engine ===
    usage_tracker = UsageTracker(redis=redis_conn, db_session_factory=None)
    quota_manager = QuotaManager(redis=redis_conn, db_session_factory=None)

    await usage_tracker.start()

    app.state.usage_tracker = usage_tracker
    app.state.quota_manager = quota_manager
    
    # Manejar Kill Switch
    from services.billing_alert_service import BillingAlertService
    billing_alert = BillingAlertService(event_bus, redis_conn, None)
    app.state.billing_alert = billing_alert

    try:
        await redis_conn.ping()
        logger.info("✅ Redis disponible (pool singleton is_active)")
    except Exception as exc:
        logger.warning(f"⚠️  Redis no disponible: {exc}")

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{config.ollama_base_url}/api/tags")
            if resp.status_code == 200:
                modelos = [m.get("name") for m in resp.json().get("models", [])]
                logger.info(f"✅ Ollama disponible. Modelos: {modelos}")
    except Exception as exc:
        logger.warning(f"⚠️  Ollama no respondió: {exc}")

    logger.info("✅ FluxAgent V2 listo")
    
    # Iniciar servidor de métricas Prometheus
    try:
        start_metrics_server(8001)
        logger.info("📊 Métricas Prometheus disponibles en http://localhost:8001/metrics")
    except Exception as e:
        logger.warning(f"⚠️  Servidor métricas no iniciado: {e}")

    # Iniciar scheduler de reset de cuotas (02:00 UTC diario)
    try:
        from tasks.quota_reset import start_quota_scheduler
        await start_quota_scheduler()
    except Exception as e:
        logger.warning(f"⚠️  Quota scheduler no iniciado: {e}")
        
    # Iniciar scheduler de RAG Sync (Sheets/Excel)
    try:
        from tasks.rag_scheduler import scheduler
        start_rag_scheduler()
        
        from tasks.followups import set_followup_scheduler
        set_followup_scheduler(scheduler)
    except Exception as e:
        logger.warning(f"⚠️  RAG Sync scheduler no iniciado: {e}")
        
    # Inicializar handlers del event_bus (Payment Followups, etc)
    try:
        from domain.events import DomainEvent
        from tasks.followups import schedule_followup
        
        async def handle_payment_completed(event: DomainEvent):
            customer_phone = event.payload.dict().get("customer_phone") or "desconocido"
            order_id = event.payload.dict().get("order_id")
            schedule_followup(customer_phone, "post_purchase_survey", {"order_id": order_id}, delay_hours=72)
            schedule_followup(customer_phone, "order_confirmation", {"order_id": order_id}, delay_minutes=1)
            
        async def handle_payment_failed(event: DomainEvent):
            customer_phone = event.payload.dict().get("customer_phone") or "desconocido"
            order_id = event.payload.dict().get("order_id")
            schedule_followup(customer_phone, "payment_pending", {"order_id": order_id}, delay_minutes=5)
            
        await event_bus.subscribe([EventType.PAYMENT_COMPLETED], handle_payment_completed, "followups_worker")
        await event_bus.subscribe([EventType.PAYMENT_FAILED], handle_payment_failed, "followups_worker")
        
        from core.event_listeners import persist_event_to_timeline
        from database import obtener_sesion
        
        async def timeline_wrapper(event):
            from database import SessionLocal
            async with SessionLocal() as db:
                await persist_event_to_timeline(event, db, redis_conn)
                
        timeline_events = [
            EventType.MESSAGE_RECEIVED, EventType.MESSAGE_SENT,
            EventType.QUOTE_GENERATED, EventType.QUOTE_ACCEPTED,
            EventType.ORDER_CREATED, EventType.PAYMENT_COMPLETED,
            EventType.PAYMENT_FAILED, EventType.BOOKING_CONFIRMED,
            EventType.HANDOFF_REQUESTED, EventType.FOLLOWUP_SCHEDULED
        ]
        await event_bus.subscribe(timeline_events, timeline_wrapper, "timeline_worker")
        
        logger.info("✅ EventBus handlers para followups registrados.")
    except Exception as e:
        logger.warning(f"⚠️ Error registrando handlers de EventBus: {e}")
    
    # ─── AGENT REGISTRY ───────────────────────────────
    from runtime.agent_registry import (
        AgentRegistry, AgentCapability
    )
    from runtime.tool_contract import ToolContract, RiskLevel
    from runtime.tool_runtime import ToolRuntime

    agent_registry = AgentRegistry()

    agent_registry.register(AgentCapability(
        agent_id="sales_agent_v1",
        name="Agente de Ventas",
        skills=["purchase", "price_check", "inquiry",
                "quote", "product_recommendation"],
        cost_per_turn=0.002,
        avg_latency_ms=800,
        priority=1,
        system_prompt=(
            "Eres un experto en ventas LATAM. "
            "Ayudas a los clientes a encontrar "
            "productos, generar cotizaciones y "
            "completar compras. Eres amable, "
            "conciso y orientado a cerrar ventas."
        ),
    ))

    agent_registry.register(AgentCapability(
        agent_id="support_agent_v1",
        name="Agente de Soporte",
        skills=["complaint", "support", "refund",
                "order_status", "troubleshooting"],
        cost_per_turn=0.002,
        avg_latency_ms=900,
        priority=2,
        system_prompt=(
            "Eres un especialista en soporte al cliente. "
            "Resuelves problemas con pedidos, gestionas "
            "devoluciones y escalas cuando es necesario. "
            "Eres empático y resolutivo."
        ),
    ))

    agent_registry.register(AgentCapability(
        agent_id="ops_agent_v1",
        name="Agente Operacional",
        skills=["booking", "reservation", "scheduling",
                "availability_check", "operations"],
        cost_per_turn=0.002,
        avg_latency_ms=700,
        priority=3,
        system_prompt=(
            "Eres un coordinador operacional. "
            "Gestionas reservas, citas y disponibilidad. "
            "Eres preciso con fechas, horarios y "
            "confirmaciones de servicio."
        ),
    ))

    # ─── TOOL RUNTIME + CONTRACTS ─────────────────────
    tool_runtime = ToolRuntime(
        tool_executor=app.state.tool_executor
        if hasattr(app.state, "tool_executor") else None,
        redis_client=app.state.redis,
    )

    contracts = [
        ToolContract(
            id="send_message",
            risk_level=RiskLevel.LOW,
            idempotent=False,
            timeout_ms=3000,
            requires_human=False,
            max_calls_per_session=50,
            side_effects=True,
            allowed_roles=[],
        ),
        ToolContract(
            id="create_order",
            risk_level=RiskLevel.HIGH,
            idempotent=False,
            timeout_ms=8000,
            requires_human=False,
            max_calls_per_session=5,
            side_effects=True,
            allowed_roles=["sales_agent", "operations_admin",
                           "ai_operator"],
        ),
        ToolContract(
            id="issue_refund",
            risk_level=RiskLevel.CRITICAL,
            idempotent=True,
            timeout_ms=10000,
            requires_human=True,
            max_calls_per_session=2,
            side_effects=True,
            allowed_roles=["operations_admin",
                           "finance_manager"],
            max_amount_allowed=500.0,
        ),
        ToolContract(
            id="check_inventory",
            risk_level=RiskLevel.LOW,
            idempotent=True,
            timeout_ms=2000,
            requires_human=False,
            max_calls_per_session=20,
            side_effects=False,
            allowed_roles=[],
        ),
        ToolContract(
            id="create_quote",
            risk_level=RiskLevel.MEDIUM,
            idempotent=False,
            timeout_ms=5000,
            requires_human=False,
            max_calls_per_session=10,
            side_effects=True,
            allowed_roles=[],
        ),
        ToolContract(
            id="get_order_status",
            risk_level=RiskLevel.LOW,
            idempotent=True,
            timeout_ms=2000,
            requires_human=False,
            max_calls_per_session=30,
            side_effects=False,
            allowed_roles=[],
        ),
        ToolContract(
            id="escalate_to_human",
            risk_level=RiskLevel.MEDIUM,
            idempotent=False,
            timeout_ms=3000,
            requires_human=False,
            max_calls_per_session=3,
            side_effects=True,
            allowed_roles=[],
        ),
    ]

    for contract in contracts:
        tool_runtime.register_contract(contract)

    app.state.agent_registry = agent_registry
    app.state.tool_runtime = tool_runtime

    logger.info(
        "runtime_bootstrap_complete",
        extra={
            "agents": len(agent_registry._agents),
            "tool_contracts": len(
                tool_runtime.tool_contracts
            ),
        },
    )
    
    yield
    logger.info("🛑 Cerrando FluxAgent V2...")
    
    try:
        from tasks.quota_reset import stop_quota_scheduler
        await stop_quota_scheduler()
    except Exception:
        pass
        
    try:
        stop_rag_scheduler()
    except Exception:
        pass
    
    if hasattr(app.state, "usage_tracker"):
        await app.state.usage_tracker.stop()
        
    if hasattr(app.state, "event_bus"):
        await app.state.event_bus.close()

    if hasattr(app.state, "redis"):
        await app.state.redis.aclose()
        await redis_pool.aclose()
        logger.info("🔴 Redis pool cerrado")

    await cerrar_db()
