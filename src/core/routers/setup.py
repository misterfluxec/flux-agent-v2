# =============================================================================
# FLUXAGENT V2 — ROUTER SETUP
# Registro centralizado de todos los routers por dominio de negocio.
# Cada sección es un dominio. Los prefijos son el contrato público de la API.
# =============================================================================

import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def _include(app: FastAPI, module_path: str, router_attr: str, **kwargs) -> bool:
    """Helper: importa y registra un router. Devuelve False sin lanzar excepción si falla."""
    try:
        import importlib
        module = importlib.import_module(module_path)
        router = getattr(module, router_attr)
        app.include_router(router, **kwargs)
        return True
    except Exception as e:
        logger.warning(f"⚠️ Router '{module_path}.{router_attr}' no cargado: {e}")
        return False


def register_routers(app: FastAPI) -> None:
    """Registra todos los routers agrupados por dominio de negocio."""
    loaded = 0
    failed = 0

    def inc(module_path, attr, **kwargs):
        nonlocal loaded, failed
        if _include(app, module_path, attr, **kwargs):
            loaded += 1
        else:
            failed += 1

    # ── Sistema / Health ───────────────────────────────────────────────────
    inc("routers.health_router",             "router", prefix="/health",          tags=["Sistema"])
    inc("routers.system_health_router",      "router", prefix="/system",          tags=["Sistema"])
    inc("routers.observability_router",      "router", prefix="/observability",   tags=["Sistema"])
    inc("routers.resilience_router",         "router", prefix="/resilience",      tags=["Sistema"])
    inc("api.telemetry.router",              "router", prefix="/telemetry",       tags=["Sistema"])
    inc("core.resilience.dlq_api",           "router", prefix="/dlq",             tags=["Sistema"])

    # ── Autenticación & Usuarios ───────────────────────────────────────────
    inc("routers.auth_router",               "router", prefix="/auth",            tags=["Auth"])
    inc("routers.users_router",              "router", prefix="/users",           tags=["Usuarios"])
    inc("routers.admin_router",              "router", prefix="/admin",           tags=["Admin"])

    # ── Planes, Facturación & Cuotas ──────────────────────────────────────
    inc("routers.billing_router",            "router", prefix="/billing",         tags=["Billing"])
    inc("routers.plans_router",              "router", prefix="/plans",           tags=["Billing"])
    inc("routers.quota_router",              "router", prefix="/quota",           tags=["Billing"])
    inc("routers.usage_router",              "router", prefix="/usage",           tags=["Billing"])
    inc("routers.invoices_router",           "router", prefix="/invoices",        tags=["Billing"])

    # ── Agentes & IA ──────────────────────────────────────────────────────
    inc("routers.agents_router",             "router", prefix="/agents",          tags=["IA"])
    inc("routers.ai_copilot_router",         "router", prefix="/copilot",         tags=["IA"])
    inc("routers.chat_router",               "router", prefix="/chat",            tags=["IA"])
    inc("routers.knowledge_router",          "router", prefix="/knowledge",       tags=["IA"])
    inc("routers.playbooks_router",          "router", prefix="/playbooks",       tags=["IA"])
    inc("routers.intelligence_router",       "router", prefix="/intelligence",    tags=["IA"])
    inc("routers.explain_router",            "router", prefix="/explain",         tags=["IA"])
    inc("routers.yanua_router",              "router", prefix="/yanua",           tags=["IA"])

    # ── Canales & WhatsApp ────────────────────────────────────────────────
    inc("routers.channels_router",           "router", prefix="/channels",        tags=["Canales"])
    inc("routers.whatsapp_router",           "router", prefix="/whatsapp",        tags=["Canales"])
    inc("routers.whatsapp_evolution_router", "router", prefix="/whatsapp/evolution", tags=["Canales"])
    inc("routers.whatsapp_cloud_router",     "router", prefix="/whatsapp/cloud",  tags=["Canales"])
    inc("routers.whatsapp_health_router",    "router", prefix="/whatsapp/health", tags=["Canales"])
    inc("routers.voice_router",              "router", prefix="/voice",           tags=["Canales"])
    inc("routers.handoff_router",            "router", prefix="/handoff",         tags=["Canales"])

    # ── CRM & Clientes ────────────────────────────────────────────────────
    inc("routers.leads_router",              "router", prefix="/leads",           tags=["CRM"])
    inc("routers.customers_router",          "router", prefix="/customers",       tags=["CRM"])
    inc("routers.onboarding_router",         "router", prefix="/onboarding",      tags=["CRM"])
    inc("routers.business_memory_router",    "router", prefix="/memory",          tags=["CRM"])
    inc("routers.timeline_router",           "router", prefix="/timeline",        tags=["CRM"])
    inc("routers.sales_agent_router",        "router", prefix="/sales",           tags=["CRM"])

    # ── Comercio & Pagos ──────────────────────────────────────────────────
    inc("routers.catalog_router",            "router", prefix="/catalog",         tags=["Comercio"])
    inc("routers.products_router",           "router", prefix="/products",        tags=["Comercio"])
    inc("routers.commerce_router",           "router", prefix="/commerce",        tags=["Comercio"])
    inc("routers.checkout_router",           "router", prefix="/checkout",        tags=["Comercio"])
    inc("routers.payments_router",           "router", prefix="/payments",        tags=["Comercio"])
    inc("routers.invoices_router",           "router", prefix="/invoices",        tags=["Comercio"])

    # ── Analytics & Reporting ─────────────────────────────────────────────
    inc("routers.analytics_router",          "router", prefix="/analytics",       tags=["Analytics"])
    inc("routers.analytics_router_cached",   "router", prefix="/analytics/cached",tags=["Analytics"])
    inc("routers.stats_router",              "router", prefix="/stats",           tags=["Analytics"])
    inc("routers.insights_router",           "router", prefix="/insights",        tags=["Analytics"])

    # ── Integraciones & Sync ──────────────────────────────────────────────
    inc("routers.integrations_router",       "router", prefix="/integrations",    tags=["Integraciones"])
    inc("routers.connectors_router",         "router", prefix="/connectors",      tags=["Integraciones"])
    inc("routers.sync_router",               "router", prefix="/sync",            tags=["Integraciones"])
    inc("routers.oauth_sync_router",         "router", prefix="/oauth",           tags=["Integraciones"])
    inc("routers.webhooks_router",           "router", prefix="/webhooks",        tags=["Integraciones"])

    # ── Ingesta & Upload ──────────────────────────────────────────────────
    inc("routers.ingest_router",             "router", prefix="/ingest",          tags=["Ingesta"])
    inc("routers.upload_router",             "router", prefix="/upload",          tags=["Ingesta"])
    inc("routers.capabilities_router",       "router", prefix="/capabilities",    tags=["Ingesta"])

    # ── Realtime & Operaciones ────────────────────────────────────────────
    inc("routers.ws_gateway_router",         "router", prefix="/ws",             tags=["Realtime"])
    inc("routers.realtime_router",           "router", prefix="/realtime",        tags=["Realtime"])
    inc("routers.event_actions_router",      "router", prefix="/actions",         tags=["Realtime"])
    inc("routers.operations_router",         "router", prefix="/operations",      tags=["Realtime"])

    logger.info(f"✅ Routers registrados: {loaded} OK, {failed} omitidos")
    if failed > 0:
        logger.warning(f"⚠️ {failed} routers no se cargaron (ver warnings arriba)")
