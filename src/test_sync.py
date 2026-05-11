import asyncio
import os
import sys

# Ajustar path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "src")))

from services.spreadsheet_sync_rag import RAGSyncEngine
from database import SesionLocal
from sqlalchemy import text

async def run_test():
    print("Obteniendo Tenant ID y Agent ID de prueba...")
    async with SesionLocal() as db:
        # Get first tenant and agent
        t_res = await db.execute(text("SELECT id FROM tenants LIMIT 1"))
        t_row = t_res.fetchone()
        if not t_row:
            print("No tenants found.")
            return
        tenant_id = str(t_row.id)
        
        a_res = await db.execute(text("SELECT id FROM agents WHERE tenant_id = :tid LIMIT 1"), {"tid": tenant_id})
        a_row = a_res.fetchone()
        agent_id = str(a_row.id) if a_row else None

        print(f"Tenant: {tenant_id}, Agent: {agent_id}")
        
        # Parse local file
        print("Leyendo local_test_catalog.csv...")
        headers, rows = await RAGSyncEngine.fetch_local_file_data("local_test_catalog.csv")
        
        print(f"Headers detectados: {headers}")
        column_mapping = RAGSyncEngine.detect_column_mapping(headers)
        print(f"Mapeo automático: {column_mapping}")
        
        print(f"Procesando {len(rows)} filas...")
        stats = await RAGSyncEngine.process_sheet_for_rag(
            tenant_id=tenant_id,
            agent_id=agent_id,
            synced_source_id="local_test_catalog.csv",
            rows=rows,
            column_mapping=column_mapping
        )
        
        print(f"Sincronización completa. Estadísticas: {stats}")
        
        # Verify in DB
        cat_res = await db.execute(text("SELECT name, base_price, stock_quantity FROM catalog_items WHERE tenant_id = :tid"), {"tid": tenant_id})
        items = cat_res.fetchall()
        print("\n--- ÍTEMS EN CATÁLOGO ---")
        for item in items:
            print(f"- {item.name}: ${item.base_price} (Stock: {item.stock_quantity})")

if __name__ == "__main__":
    asyncio.run(run_test())
