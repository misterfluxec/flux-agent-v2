from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from auth import get_usuario_actual, PayloadToken
from database import obtener_sesion as get_db

router = APIRouter(prefix="/api/v1", tags=["Chat"])

@router.get("/chat/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    usuario: PayloadToken = Depends(get_usuario_actual),
):
    """Historial de mensajes de una conversación."""
    tid = str(usuario.tenant_id)
    await db.execute(text("SELECT set_config('app.current_tenant_id', :tenant_id, true)"), {"tenant_id": tid})
    r = await db.execute(
        text("""
            SELECT m.rol as role,
                   m.contenido as content,
                   m.creado_en::text as timestamp
            FROM mensajes m
            JOIN conversaciones c
              ON m.conversacion_id=c.id
            WHERE m.conversacion_id=:cid
              AND c.tenant_id=:tid
            ORDER BY m.creado_en ASC
        """),
        {"cid": conversation_id,
         "tid": tid},
    )
    return [
        {"role": row.role,
         "content": row.content,
         "timestamp": row.timestamp}
        for row in r.fetchall()
    ]
