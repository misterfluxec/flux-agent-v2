import asyncio
import os
import asyncpg
from dotenv import load_dotenv

async def run_migration():
    load_dotenv('.env')
    url = os.getenv('DATABASE_URL')
    if not url:
        print('No DATABASE_URL found')
        return
    
    # We use asyncpg directly to avoid SQLAlchemy colon parsing issues
    try:
        conn = await asyncpg.connect(url)
        with open('migrations/013_business_core.sql', 'r') as f:
            sql = f.read()
        await conn.execute(sql)
        print('✅ Migration executed successfully.')
        await conn.close()
    except Exception as e:
        print(f'Error executing migration: {e}')

if __name__ == '__main__':
    asyncio.run(run_migration())
