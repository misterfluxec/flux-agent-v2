import asyncio
import os
import sys

# Añadir el path para importar database
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from database import engine

async def create_table():
    sql = """
    CREATE TABLE IF NOT EXISTS connected_channels (
        id UUID PRIMARY KEY,
        tenant_id UUID NOT NULL,
        channel_type TEXT NOT NULL,
        status TEXT NOT NULL,
        external_session_id TEXT,
        config JSONB,
        health_score INT DEFAULT 100,
        last_heartbeat TIMESTAMP,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """
    try:
        async with engine.begin() as conn:
            await conn.execute(text(sql))
            print("Table connected_channels created successfully.")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_table())
