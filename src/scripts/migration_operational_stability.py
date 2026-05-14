import asyncio
import os
import sys

# Añadir el path para importar database
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import text
from database import engine

async def migrate():
    sqls = [
        """
        CREATE TABLE IF NOT EXISTS channel_dead_letters (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            provider_name TEXT NOT NULL,
            correlation_id TEXT,
            event_type TEXT NOT NULL,
            payload JSONB NOT NULL,
            error_reason TEXT,
            retry_count INT DEFAULT 0,
            max_retries INT DEFAULT 3,
            next_retry_at TIMESTAMP,
            resolved_at TIMESTAMP,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        """,
        """
        CREATE TABLE IF NOT EXISTS event_outbox (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            sequence BIGSERIAL UNIQUE,
            event_type TEXT NOT NULL,
            correlation_id TEXT,
            idempotency_key TEXT,
            payload JSONB NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        "CREATE INDEX IF NOT EXISTS idx_outbox_tenant_seq ON event_outbox (tenant_id, sequence);",
        "CREATE INDEX IF NOT EXISTS idx_outbox_idemp ON event_outbox (idempotency_key);",
        """
        CREATE TABLE IF NOT EXISTS channel_metrics_hourly (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            channel_type TEXT NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value NUMERIC NOT NULL,
            time_bucket TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """,
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_channel_metrics_hourly_unique ON channel_metrics_hourly(tenant_id, channel_type, metric_name, time_bucket);"
    ]
    try:
        async with engine.begin() as conn:
            for sql in sqls:
                await conn.execute(text(sql))
            print("Operational Stability tables created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
