# =============================================================================
# FLUXAGENT V2 — DYNAMIC ROUTER LOADER
# =============================================================================

import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def setup_routers(app: FastAPI):
    """
    Registra todos los routers de la aplicación de forma unificada.
    Permite limpiar main.py y facilita la habilitación condicional de módulos.
    """
    from routers.auth_router import router as auth_router
    from routers.usage_router import router as usage_router
    from routers.catalog_router import router as catalog_router
    from routers.whatsapp_router import router as whatsapp_router
    from routers.webhooks_router import router as webhooks_router
    from routers.leads_router import router as leads_router
    from routers.admin_router import router as admin_router
    from routers.users_router import router as users_router
    from routers.agents_router import router as agents_router
    from routers.payments_router import router as payments_router
    from routers.ingest_router import router as ingest_router, ws_router
    from routers.voice_router import router as voice_router
    from routers.channels_router import router as channels_router
    from routers.whatsapp_health_router import router as whatsapp_health_router
    from routers.health_router import router as health_router
    from routers.whatsapp_cloud_router import router as whatsapp_cloud_router
    from routers.quota_router import router as quota_router
    from routers.oauth_sync_router import router as oauth_sync_router
    from routers.sync_router import router as sync_router
    from routers.upload_router import router as upload_router
    from routers.analytics_router import router as analytics_router
    from routers.billing_router import router as billing_router
    from routers.plans_router import router as plans_router
    from routers.stats_router import router as stats_router
    
    # Nuevos routers API de infraestructura
    from api.telemetry.router import router as telemetry_router
    from core.resilience.dlq_api import router as dlq_router
    from routers.ws_gateway_router import router as ws_gateway_router
    from routers.handoff_router import router as handoff_router
    from routers.insights_router import router as insights_router
    from routers.explain_router import router as explain_router
    from routers.yanua_router import router as yanua_router
    from routers.commerce_router import router as commerce_router
    from routers.checkout_router import router as checkout_router
    from routers.onboarding_router import router as onboarding_router
    from routers.timeline_router import router as timeline_router
    from routers.capabilities_router import router as capabilities_router
    from routers.playbooks_router import router as playbooks_router
    from routers.event_actions_router import router as event_actions_router
    from routers.connectors_router import router as connectors_router
    from routers.ai_copilot_router import router as ai_copilot_router
    from routers.chat_router import router as main_chat_router
    from routers.knowledge_router import router as knowledge_router
    from routers.whatsapp_evolution_router import router as whatsapp_evolution_router
    from api.routers.enterprise_router import router as enterprise_router

    # Base & Core
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(users_router)
    app.include_router(health_router)
    app.include_router(whatsapp_health_router)
    
    # Billing & Usage
    app.include_router(usage_router)
    app.include_router(billing_router)
    app.include_router(plans_router)
    app.include_router(quota_router)
    app.include_router(payments_router)
    
    # Core & Infra
    app.include_router(upload_router)
    app.include_router(telemetry_router)
    app.include_router(dlq_router)
    
    # Integrations
    app.include_router(catalog_router)
    app.include_router(ingest_router)
    app.include_router(ws_router)
    app.include_router(upload_router)
    app.include_router(oauth_sync_router)
    app.include_router(sync_router)
    app.include_router(connectors_router)
    
    # AI & Agents
    app.include_router(agents_router)
    app.include_router(ai_copilot_router)
    app.include_router(capabilities_router)
    app.include_router(playbooks_router)
    
    # Channels
    app.include_router(whatsapp_router)
    app.include_router(whatsapp_evolution_router)
    app.include_router(whatsapp_cloud_router)
    app.include_router(webhooks_router)
    app.include_router(voice_router)
    app.include_router(channels_router)
    
    # Operations & Analytics
    app.include_router(main_chat_router)
    app.include_router(knowledge_router)
    app.include_router(leads_router)
    app.include_router(analytics_router)
    app.include_router(stats_router)
    app.include_router(insights_router, prefix="/api/v1")
    app.include_router(explain_router, prefix="/api/v1")
    app.include_router(yanua_router, prefix="/api/v1")
    app.include_router(commerce_router)
    app.include_router(checkout_router)
    app.include_router(onboarding_router)
    app.include_router(timeline_router)
    app.include_router(event_actions_router)
    app.include_router(handoff_router)
    app.include_router(enterprise_router)
    
    # Gateways
    app.include_router(ws_gateway_router)

    logger.info("✅ 35+ Routers inicializados exitosamente")
