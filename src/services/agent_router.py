# src/services/agent_router.py
from database import sesion_db
from sqlalchemy import text
from typing import Optional
from .intent_classifier import classify_intent

async def resolve_agent_for_channel(tenant_id: str, channel: str, message_text: Optional[str] = None) -> str:
    """
    Devuelve el agent_id correcto según canal e intención.
    """
    intent = classify_intent(message_text) if message_text else 'general'
    
    async with sesion_db() as db:
        agent = None
        
        target_types = []
        if intent == 'support':
            target_types = ['support']
        elif intent == 'bookings':
            target_types = ['bookings']
        elif intent == 'sales':
            target_types = ['sales']
        else:
            target_types = ['sales', 'support', 'bookings']
            
        for agent_type in target_types:
            query = "SELECT id FROM agents WHERE tenant_id = :tid AND agent_type = :type AND estado = 'activo' LIMIT 1"
            result = await db.execute(text(query), {"tid": tenant_id, "type": agent_type})
            agent = result.fetchone()
            if agent:
                break

        if not agent:
            # Fallback a cualquiera activo
            fallback = await db.execute(text("SELECT id FROM agents WHERE tenant_id = :tid AND estado = 'activo' LIMIT 1"), {"tid": tenant_id})
            agent = fallback.fetchone()
            
        if not agent:
            raise ValueError("No hay agentes activos configurados para este tenant.")
            
        return str(agent.id)
