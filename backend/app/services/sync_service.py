import httpx
import logging

logger = logging.getLogger(__name__)

async def pull_shopify_products(store_url: str, api_key: str, password: str) -> list:
    """Obtiene productos de Shopify vía REST Admin API"""
    url = f"{store_url}/admin/api/2024-01/products.json"
    auth = (api_key, password)
    async with httpx.AsyncClient(auth=auth) as client:
        resp = await client.get(url, params={"limit": 250})
        resp.raise_for_status()
        return resp.json().get("products", [])

async def push_to_rag(tenant_id: str, products: list):
    """Convierte productos en chunks vectoriales para el agente"""
    # Esta función se integrará con el servicio de Knowledge de la Fase 4
    logger.info(f"🚀 Sincronizando {len(products)} productos para tenant {tenant_id} en RAG")
    for p in products:
        # Mock de procesamiento de RAG
        content = f"Producto: {p['title']}. Precio: ${p['variants'][0]['price']}. Stock: {p['variants'][0]['inventory_quantity']}."
        # Aquí llamarías a vector_db.upsert(...)
    return True
