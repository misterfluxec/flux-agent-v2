import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def _safe_include(app: FastAPI, import_path: str, attr: str = "router", **kwargs):
    """Registra un router con fail-safe — un fallo no bloquea el resto."""
    try:
        module = __import__(import_path, fromlist=[attr])
        router = getattr(module, attr)
        app.include_router(router, **kwargs)
    except Exception as e:
        logger.warning(f"⚠️ Router '{import_path}.{attr}' no cargó: {e}")

def register_routers(app: FastAPI):
    # 🔐 Auth & Security
    _safe_include(app, "routers.auth_router")

    # 💼 Billing & Usage
    _safe_include(app, "routers.billing_router")
    _safe_include(app, "routers.plans_router")
    _safe_include(app, "routers.quota_router")
    _safe_include(app, "routers.usage_router")

    # 🤖 AI & Agents
    _safe_include(app, "routers.agents_router")
    _safe_include(app, "routers.ai_copilot_router")
    _safe_include(app, "routers.voice_router")

    # 📡 Channels & Webhooks
    _safe_include(app, "routers.whatsapp_evolution_router")
    _safe_include(app, "routers.whatsapp_cloud_router")
    _safe_include(app, "routers.webhooks_router")
    _safe_include(app, "routers.channels_router")
    _safe_include(app, "routers.whatsapp_router")
    _safe_include(app, "routers.whatsapp_health_router")

    # 📦 Operations & Commerce
    _safe_include(app, "routers.leads_router")
    _safe_include(app, "routers.catalog_router")
    _safe_include(app, "routers.commerce_router")
    _safe_include(app, "routers.checkout_router")
    _safe_include(app, "routers.playbooks_router")
    _safe_include(app, "routers.sales_agent_router")
    _safe_include(app, "routers.onboarding_router")
    _safe_include(app, "routers.yanua_router", prefix="/api/v1")

    # 📊 Analytics & Insights
    _safe_include(app, "routers.analytics_router")
    _safe_include(app, "routers.insights_router", prefix="/api/v1")
    _safe_include(app, "routers.timeline_router")
    _safe_include(app, "routers.explain_router", prefix="/api/v1")

    # ⚙️ Integrations & Sync
    _safe_include(app, "routers.ingest_router")
    _safe_include(app, "routers.ingest_router", attr="ws_router")  # WebSocket de ingesta
    _safe_include(app, "routers.sync_router")
    _safe_include(app, "routers.connectors_router")
    _safe_include(app, "routers.oauth_sync_router")
    _safe_include(app, "routers.upload_router")

    # 🛡️ System & Admin
    _safe_include(app, "routers.health_router")
    _safe_include(app, "routers.admin_router")
    _safe_include(app, "routers.users_router")
    _safe_include(app, "routers.ws_gateway_router")
    _safe_include(app, "routers.resilience_router")
    _safe_include(app, "routers.handoff_router")
    _safe_include(app, "routers.capabilities_router")
    _safe_include(app, "routers.event_actions_router")

    # 🏛️ Enterprise & Governance
    _safe_include(app, "api.routers.governance_router")
    _safe_include(app, "api.routers.enterprise_router")
    _safe_include(app, "api.routers.workflows_router")
    _safe_include(app, "core.resilience.dlq_api")

    # 🏠 Root endpoints (/, /health, /api/v1/knowledge)
    from core.routers.root_endpoints import register_root_endpoints
    register_root_endpoints(app)

    logger.info("✅ Routers registrados por dominio (fail-safe individual)")
