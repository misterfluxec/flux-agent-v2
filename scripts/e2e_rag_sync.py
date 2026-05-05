import asyncio
import uuid
from httpx import AsyncClient
from unittest.mock import patch

from main import app
from auth import crear_token_acceso

# Mock de datos
MOCK_SHEET_DATA = (
    ["nombre", "precio", "stock", "sku", "categoria", "descripcion"],
    [
        {"nombre": "Laptop Pro", "precio": "1200", "stock": "15", "sku": "LP-001", "categoria": "Laptops", "descripcion": "Potente laptop para devs"},
        {"nombre": "Mouse Inalámbrico", "precio": "25", "stock": "50", "sku": "MS-002", "categoria": "Accesorios", "descripcion": "Ergonómico y veloz"},
        {"nombre": "Monitor 4K", "precio": "350", "stock": "10", "sku": "MN-003", "categoria": "Monitores", "descripcion": "Colores precisos"}
    ]
)

async def test_e2e_rag_sync_flow():
    # 1. Configurar Entorno DB Inicial vía SQL crudo en Test
    import subprocess
    tenant_id = str(uuid.uuid4())
    agent_id = str(uuid.uuid4())
    account_id = str(uuid.uuid4())
    source_id = str(uuid.uuid4())
    
    sql_setup = f"""
    INSERT INTO tenants (id, nombre, estado) VALUES ('{tenant_id}', 'Tenant E2E', 'activo');
    INSERT INTO agents (id, tenant_id, nombre, estado, modelo) VALUES ('{agent_id}', '{tenant_id}', 'FluxAgent', 'active', 'nomic-embed-text');
    INSERT INTO connected_accounts (id, tenant_id, provider, provider_user_id, provider_email, access_token_encrypted, is_active)
    VALUES ('{account_id}', '{tenant_id}', 'google', 'user123', 'test@test.com', 'ENCRYPTED_MOCK', true);
    INSERT INTO synced_sources (id, tenant_id, account_id, agent_id, source_type, source_id, source_name, column_mapping)
    VALUES ('{source_id}', '{tenant_id}', '{account_id}', '{agent_id}', 'google_sheets', 'SHEET123', 'Inventario Test', '{{"nombre": "nombre", "precio": "precio"}}');
    """
    
    # We will just run this SQL directly in python using psycopg2 since we are already inside the container
    # Wait, the app has obtaining db sessions. But we can use subprocess calling psql since it's in the network. Or just use the fastapi db.
    import asyncpg
    from config import obtener_config
    config = obtener_config()
    
    # Simple db connection to insert mock data
    conn = await asyncpg.connect(config.database_url)
    await conn.execute(f"INSERT INTO tenants (id, nombre, estado) VALUES ('{tenant_id}', 'Tenant E2E', 'activo')")
    await conn.execute(f"INSERT INTO agents (id, tenant_id, nombre, estado, modelo) VALUES ('{agent_id}', '{tenant_id}', 'FluxAgent', 'active', 'nomic-embed-text')")
    await conn.execute(f"INSERT INTO connected_accounts (id, tenant_id, provider, provider_user_id, provider_email, access_token_encrypted, is_active) VALUES ('{account_id}', '{tenant_id}', 'google', 'user123', 'test@test.com', 'ENCRYPTED_MOCK', true)")
    await conn.execute(f"INSERT INTO synced_sources (id, tenant_id, account_id, agent_id, source_type, source_id, source_name, column_mapping) VALUES ('{source_id}', '{tenant_id}', '{account_id}', '{agent_id}', 'google_sheets', 'SHEET123', 'Inventario Test', '{{\"nombre\": \"nombre\", \"precio\": \"precio\"}}')")
    await conn.close()

    # Autenticación
    token = crear_token_acceso(data={"sub": "usuario_test", "tenant_id": tenant_id, "rol": "admin"})
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Mockear la obtención de datos de Google y la Desencriptación
    with patch('services.spreadsheet_sync_rag.RAGSyncEngine.fetch_google_sheet_data', return_value=MOCK_SHEET_DATA), \
         patch('core.encryption.EncryptionService.decrypt', return_value="FAKE_TOKEN"):
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # A. Disparar Sincronización
            payload = {
                "agent_id": agent_id,
                "source_id": source_id,
                "account_id": account_id,
                "column_mapping": {"nombre": "nombre", "precio": "precio", "stock": "stock"},
                "sync_frequency": "daily"
            }
            
            response = await client.post("/api/v1/sync/sheets", json=payload, headers=headers)
            assert response.status_code == 202
            data = response.json()
            assert "job_id" in data
            job_id = data["job_id"]
            
            # B. Polling hasta que termine (Background Task)
            import time
            status_data = {}
            for _ in range(15):  # Esperar max 15 segundos
                await asyncio.sleep(1)
                status_resp = await client.get(f"/api/v1/sync/jobs/{job_id}/status", headers=headers)
                assert status_resp.status_code == 200
                status_data = status_resp.json()
                if status_data["status"] in ["success", "failed"]:
                    break
                    
            assert status_data["status"] == "success"
            assert status_data["rows_processed"] == 3
            
            # C. Verificar GET /agents con subconsulta RAG
            agents_resp = await client.get("/api/v1/agents", headers=headers)
            assert agents_resp.status_code == 200
            agents_data = agents_resp.json()
            
            # Debería haber un agente y su knowledge_base_size debe ser 3
            agent = agents_data["agents"][0]
            assert agent["nombre"] == "Yanua"
            assert agent["knowledge_base_size"] == 3
            assert agent["last_sync_at"] is not None

    print("✅ TEST E2E PASADO: OAuth -> Sheets -> Ollama -> DB PgVector -> UI API")

if __name__ == "__main__":
    asyncio.run(test_e2e_rag_sync_flow())
