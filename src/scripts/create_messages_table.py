import asyncio
from sqlalchemy import text
from database import obtener_sesion

async def migrate():
    async with obtener_sesion() as db:
        print("Creando tabla de mensajes_chat...")
        query = """
        CREATE TABLE IF NOT EXISTS mensajes_chat (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            contenido TEXT NOT NULL,
            timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            tokens_count INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_mensajes_session ON mensajes_chat(tenant_id, session_id);
        """
        await db.execute(text(query))
        await db.commit()
        print("Migración completada exitosamente.")

if __name__ == "__main__":
    asyncio.run(migrate())
