import os
import shutil

ROUTERS_DIR = "routers"
API_ROUTERS_DIR = "api/routers"

DOMAINS = {
    "auth": ["auth_router.py", "users_router.py", "oauth_sync_router.py"],
    "billing": ["billing_router.py", "plans_router.py", "quota_router.py", "usage_router.py", "invoices_router.py", "payments_router.py"],
    "agents": ["agents_router.py", "ai_copilot_router.py", "voice_router.py", "sales_agent_router.py", "yanua_router.py", "knowledge_router.py", "business_memory_router.py"],
    "communications": ["whatsapp_evolution_router.py", "webhooks_router.py", "channels_router.py", "chat_router.py", "realtime_router.py", "ws_gateway_router.py"],
    "commerce": ["catalog_router.py", "commerce_router.py", "checkout_router.py", "products_router.py", "leads_router.py", "customers_router.py"],
    "analytics": ["analytics_router.py", "analytics_router_cached.py", "insights_router.py", "stats_router.py", "timeline_router.py"],
    "integrations": ["connectors_router.py", "sync_router.py", "ingest_router.py", "upload_router.py", "integrations_router.py"],
    "system": ["health_router.py", "admin_router.py", "resilience_router.py", "system_health_router.py", "observability_router.py"],
    "operations": ["operations_router.py", "handoff_router.py", "playbooks_router.py", "capabilities_router.py", "event_actions_router.py", "explain_router.py"]
}

# Routers a eliminar
TO_DELETE = ["whatsapp_cloud_router.py", "whatsapp_router.py", "whatsapp_health_router.py"]

os.makedirs(API_ROUTERS_DIR, exist_ok=True)

moved_files = []

for domain, files in DOMAINS.items():
    domain_dir = os.path.join(API_ROUTERS_DIR, domain)
    os.makedirs(domain_dir, exist_ok=True)
    # create __init__.py so it is a module
    open(os.path.join(domain_dir, "__init__.py"), "a").close()
    
    for f in files:
        src = os.path.join(ROUTERS_DIR, f)
        dst = os.path.join(domain_dir, f)
        if os.path.exists(src):
            shutil.move(src, dst)
            moved_files.append((f, domain))

# Eliminar duplicados de whatsapp
for f in TO_DELETE:
    src = os.path.join(ROUTERS_DIR, f)
    if os.path.exists(src):
        os.remove(src)

# Crear un nuevo registry.py
registry_code = f"""import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def _safe_include(app: FastAPI, import_path: str, attr: str = "router", **kwargs):
    try:
        module = __import__(import_path, fromlist=[attr])
        router = getattr(module, attr)
        app.include_router(router, **kwargs)
    except Exception as e:
        logger.warning(f"⚠️ Router '{{import_path}}.{{attr}}' no cargó: {{e}}")

def register_routers(app: FastAPI):
"""

for domain, files in DOMAINS.items():
    registry_code += f"    # {domain.upper()}\n"
    for f in files:
        module_name = f.replace('.py', '')
        if f == "yanua_router.py" or f == "insights_router.py" or f == "explain_router.py":
            registry_code += f'    _safe_include(app, "api.routers.{domain}.{module_name}", prefix="/api/v1")\n'
        else:
            registry_code += f'    _safe_include(app, "api.routers.{domain}.{module_name}")\n'
        if f == "ingest_router.py":
            registry_code += f'    _safe_include(app, "api.routers.{domain}.{module_name}", attr="ws_router")\n'
    registry_code += "\n"

# Reagregar governance y root
registry_code += """    # 🏛️ Enterprise & Governance
    _safe_include(app, "api.routers.governance_router")
    _safe_include(app, "api.routers.enterprise_router")
    _safe_include(app, "api.routers.workflows_router")
    _safe_include(app, "core.resilience.dlq_api")

    # 🏠 Root endpoints (/, /health, /api/v1/knowledge)
    from core.routers.root_endpoints import register_root_endpoints
    register_root_endpoints(app)

    logger.info("✅ Routers registrados por dominio (fail-safe individual)")
"""

with open("core/routers/registry.py", "w") as f:
    f.write(registry_code)

print(f"✅ Migración completada. Movidos {len(moved_files)} routers. Borrados {len(TO_DELETE)} archivos antiguos.")
