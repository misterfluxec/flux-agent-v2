import asyncio
import os
from uuid import UUID

os.environ["LLM_MODE"] = "local"

from routers.chat_router import procesar_mensaje_entrante

async def run_test():
    from database import SesionLocal
    from sqlalchemy import text
    
    tenant_id = UUID("11111111-1111-1111-1111-111111111111")
    agent_id = UUID("00000000-0000-0000-0000-000000000000")
    
    async with SesionLocal() as db:
        await db.execute(text("""
            INSERT INTO agents (id, tenant_id, name, model, instructions)
            VALUES (:aid, :tid, 'Yanua', 'qwen2.5:3b', 'Eres Yanua, una agente de ventas. Usa las herramientas provistas para verificar stock y crear órdenes.')
            ON CONFLICT DO NOTHING
        """), {"aid": str(agent_id), "tid": str(tenant_id)})
        await db.commit()
    
    print("\n--- TEST: Verificando Stock ---")
    response = await procesar_mensaje_entrante(
        tenant_id=tenant_id,
        agent_id=agent_id,
        canal="test",
        lead_externo_id="user_test_123",
        mensaje_texto="Hola, necesito saber el price y stock de la Cámara de Seguridad WiFi",
        instancia_nombre=None
    )
    print("Agent Response:", response)
    
    print("\n--- TEST: Creando Orden ---")
    response2 = await procesar_mensaje_entrante(
        tenant_id=tenant_id,
        agent_id=agent_id,
        canal="test",
        lead_externo_id="user_test_123",
        mensaje_texto="Quiero comprar 2 unidades, hazme el pedido por favor.",
        instancia_nombre=None
    )
    print("Agent Response:", response2)

if __name__ == "__main__":
    asyncio.run(run_test())
