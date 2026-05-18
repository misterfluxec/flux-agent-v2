import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def _safe_include(app: FastAPI, import_path: str, attr: str = "router", **kwargs):
    try:
        module = __import__(import_path, fromlist=[attr])
        router = getattr(module, attr)
        app.include_router(router, **kwargs)
    except Exception as e:
        logger.warning(f"⚠️ Router '{import_path}.{attr}' no cargó: {e}")

def register_routers(app: FastAPI):
    # AUTH
    _safe_include(app, "api.routers.auth.auth_router")
    _safe_include(app, "api.routers.auth.users_router")
    _safe_include(app, "api.routers.auth.oauth_sync_router")

    # BILLING
    _safe_include(app, "api.routers.billing.billing_router")
    _safe_include(app, "api.routers.billing.plans_router")
    _safe_include(app, "api.routers.billing.quota_router")
    _safe_include(app, "api.routers.billing.usage_router")
    _safe_include(app, "api.routers.billing.invoices_router")
    _safe_include(app, "api.routers.billing.payments_router")

    # AGENTS
    _safe_include(app, "api.routers.agents.agents_router")
    _safe_include(app, "api.routers.agents.ai_copilot_router")
    _safe_include(app, "api.routers.agents.voice_router")
    _safe_include(app, "api.routers.agents.sales_agent_router")
    _safe_include(app, "api.routers.agents.yanua_router", prefix="/api/v1")
    _safe_include(app, "api.routers.agents.knowledge_router")
    _safe_include(app, "api.routers.agents.business_memory_router")

    # COMMUNICATIONS
    _safe_include(app, "api.routers.communications.whatsapp_evolution_router")
    _safe_include(app, "api.routers.communications.webhooks_router")
    _safe_include(app, "api.routers.communications.channels_router")
    _safe_include(app, "api.routers.communications.chat_router")
    _safe_include(app, "api.routers.communications.realtime_router")
    _safe_include(app, "api.routers.communications.ws_gateway_router")

    # COMMERCE
    _safe_include(app, "api.routers.commerce.catalog_router")
    _safe_include(app, "api.routers.commerce.commerce_router")
    _safe_include(app, "api.routers.commerce.checkout_router")
    _safe_include(app, "api.routers.commerce.products_router")
    _safe_include(app, "api.routers.commerce.leads_router")
    _safe_include(app, "api.routers.commerce.customers_router")

    # ANALYTICS
    _safe_include(app, "api.routers.analytics.analytics_router")
    _safe_include(app, "api.routers.analytics.analytics_router_cached")
    _safe_include(app, "api.routers.analytics.insights_router", prefix="/api/v1")
    _safe_include(app, "api.routers.analytics.stats_router")
    _safe_include(app, "api.routers.analytics.timeline_router")

    # INTEGRATIONS
    _safe_include(app, "api.routers.integrations.connectors_router")
    _safe_include(app, "api.routers.integrations.sync_router")
    _safe_include(app, "api.routers.integrations.ingest_router")
    _safe_include(app, "api.routers.integrations.ingest_router", attr="ws_router")
    _safe_include(app, "api.routers.integrations.upload_router")
    _safe_include(app, "api.routers.integrations.integrations_router")

    # SYSTEM
    _safe_include(app, "api.routers.system.health_router")
    _safe_include(app, "api.routers.system.admin_router")
    _safe_include(app, "api.routers.system.resilience_router")
    _safe_include(app, "api.routers.system.system_health_router")
    _safe_include(app, "api.routers.system.observability_router")

    # OPERATIONS
    _safe_include(app, "api.routers.operations.operations_router")
    _safe_include(app, "api.routers.operations.handoff_router")
    _safe_include(app, "api.routers.operations.playbooks_router")
    _safe_include(app, "api.routers.operations.capabilities_router")
    _safe_include(app, "api.routers.operations.event_actions_router")
    _safe_include(app, "api.routers.operations.explain_router", prefix="/api/v1")

    # 🏛️ Enterprise & Governance
    _safe_include(app, "api.routers.governance_router")
    _safe_include(app, "api.routers.enterprise_router")
    _safe_include(app, "api.routers.workflows_router")
    _safe_include(app, "core.resilience.dlq_api")

    # 🏠 Root endpoints (/, /health, /api/v1/knowledge)
    from core.routers.root_endpoints import register_root_endpoints
    register_root_endpoints(app)

    logger.info("✅ Routers registrados por dominio (fail-safe individual)")
