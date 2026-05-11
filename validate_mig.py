import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def validate():
    load_dotenv('.env')
    conn = await asyncpg.connect(os.getenv('DATABASE_URL'))
    
    # 2.1 Tablas creadas
    tables = ['customers', 'payments', 'operational_invoices', 'tenant_subscriptions', 'inventory_transactions']
    print("--- TABLES ---")
    for t in tables:
        exists = await conn.fetchval('SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)', t)
        print(f"{t} exists: {exists}")
        
    print("\n--- ERP-READY FIELDS ---")
    cols = await conn.fetch("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'customers' AND column_name IN ('external_id', 'churn_score')")
    for c in cols:
        print(f"Customer field: {c['column_name']} ({c['data_type']})")

    # 2.2 RLS activo
    print("\n--- RLS STATUS ---")
    for t in tables:
        rls = await conn.fetchval("SELECT relrowsecurity FROM pg_class WHERE relname = $1", t)
        print(f"{t} RLS active: {rls}")
        
    # 2.3 Indexes
    print("\n--- INDEXES ---")
    indexes = await conn.fetch("SELECT indexname FROM pg_indexes WHERE tablename = 'payments'")
    for idx in indexes:
        print(f"Payment index: {idx['indexname']}")
        
    await conn.close()

if __name__ == '__main__':
    asyncio.run(validate())
