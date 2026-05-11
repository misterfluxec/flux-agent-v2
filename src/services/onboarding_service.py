import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from services.templates.business_profiles import BUSINESS_PROFILES
import json

logger = logging.getLogger(__name__)

async def apply_business_profile(tenant_id: str, profile_key: str, db: AsyncSession) -> dict:
    """Aplica catálogo, recursos y flujos base según el perfil elegido mediante queries raw"""
    profile = BUSINESS_PROFILES.get(profile_key)
    if not profile:
        raise ValueError(f"Perfil '{profile_key}' no encontrado")

    items_created = 0
    resources_created = 0

    # 1. Crear Business Offers (Catálogo)
    for item_data in profile.get("catalog_seed", []):
        query = text("""
            INSERT INTO business_offers 
            (tenant_id, name, type, base_price, stock_quantity, sales_playbook, commercial_strategy, is_active)
            VALUES 
            (:tenant_id, :name, :type, :base_price, :stock_quantity, :sales_playbook, :commercial_strategy, true)
        """)
        
        # Preparar JSONs
        sales_playbook = json.dumps(item_data.get("sales_playbook", {}))
        commercial_strategy = json.dumps(item_data.get("commercial_strategy", {}))
        
        await db.execute(query, {
            "tenant_id": tenant_id,
            "name": item_data.get("name"),
            "type": item_data.get("type"),
            "base_price": item_data.get("base_price", 0.0),
            "stock_quantity": item_data.get("stock_quantity"),
            "sales_playbook": sales_playbook,
            "commercial_strategy": commercial_strategy
        })
        items_created += 1

    # 2. Crear Resources
    for res_data in profile.get("resources_seed", []):
        query = text("""
            INSERT INTO resources (tenant_id, name, type, capacity, is_active)
            VALUES (:tenant_id, :name, :type, :capacity, true)
        """)
        await db.execute(query, {
            "tenant_id": tenant_id,
            "name": res_data.get("name"),
            "type": res_data.get("type"),
            "capacity": res_data.get("capacity", 1)
        })
        resources_created += 1
        
    await db.commit()
    logger.info(f"Perfil {profile_key} aplicado para tenant {tenant_id}. Ofertas: {items_created}, Recursos: {resources_created}")
    
    return {
        "message": f"Perfil '{profile['name']}' aplicado correctamente.",
        "items_created": items_created,
        "resources_created": resources_created,
        "next_step": "connect_channel"
    }
