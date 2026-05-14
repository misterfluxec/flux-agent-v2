import asyncio
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from database import engine

async def migrate():
    sqls = [
        # Drop existing non-unique index
        "DROP INDEX IF EXISTS idx_outbox_idemp;",
        
        # Add idempotency_expires_at column if not exists
        """
        ALTER TABLE event_outbox 
        ADD COLUMN IF NOT EXISTS idempotency_expires_at TIMESTAMP;
        """,
        
        # Create UNIQUE index
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_outbox_idempotency_unique 
        ON event_outbox (tenant_id, event_type, idempotency_key)
        WHERE idempotency_key IS NOT NULL;
        """
    ]
    try:
        async with engine.begin() as conn:
            for sql in sqls:
                await conn.execute(text(sql))
            print("Idempotency migration applied successfully.")
    except Exception as e:
        print(f"Error applying migration: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
