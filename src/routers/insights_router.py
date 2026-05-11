from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from database import obtener_sesion

router = APIRouter(prefix="/insights", tags=["operational-intelligence"])

@router.get("/feed")
async def get_recommendations(
    # tenant_id lo sacaríamos del token en tu auth. Por ahora mock para no romper el test:
    db: AsyncSession = Depends(obtener_sesion)
):
    """Feed determinístico de recomendaciones operativas (Heurística rápida)"""
    now = datetime.now(timezone.utc)
    
    # IMPORTANTE: Adaptado a AsyncSession y SQLAlchemy 2.0+
    # TODO: Integrar con tus tablas reales cuando Lead/Conversation existan en src.models
    hot_leads = 3 # mock heurístico
    pending_handoffs = 2
    rag_gaps = 3
    
    feed = []
    if hot_leads > 0:
        feed.append({
            "id": "hot_leads",
            "type": "insight",
            "title": f"{hot_leads} lead caliente pendiente de atención",
            "context": "El score >80 + tiempo sin respuesta indica riesgo de pérdida.",
            "actions": [{"label": "👁️ Ver en Operaciones", "variant": "primary"}]
        })
    if pending_handoffs > 0:
        feed.append({
            "id": "handoffs",
            "type": "action",
            "title": f"{pending_handoffs} conversación requiere humano",
            "context": "Yanua derivó por frustración o complejación comercial.",
            "actions": [{"label": "👤 Tomar control", "variant": "primary"}]
        })
    if rag_gaps >= 3:
        feed.append({
            "id": "knowledge_gap",
            "type": "policy",
            "title": "Brecha detectada en Inteligencia",
            "context": f"{rag_gaps} consultas sin respuesta en 72h. Actualiza documentos.",
            "actions": [{"label": "📚 Ir a Inteligencia", "variant": "outline"}]
        })
        
    return {"feed": feed, "generated_at": now.isoformat()}
