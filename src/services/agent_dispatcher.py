# src/services/agent_dispatcher.py
from sqlalchemy import text
from database import obtener_sesion, sesion_db
from .intent_classifier import classify_intent

async def get_active_agent_prompt(tenant_id: str, message: str) -> str:
    """
    Selecciona el mejor agente para el mensaje dado.
    Si no hay coincidencia exacta, retorna un agente genérico is_active.
    """
    intent = classify_intent(message)
    
    # Mapeo de intención a type de agente
    target_types = []
    if intent == 'support':
        target_types = ['support']
    elif intent == 'bookings':
        target_types = ['bookings']
    elif intent == 'sales':
        target_types = ['sales']
    else:
        target_types = ['sales', 'support', 'bookings'] # Fallback order

    # Query a la BD para encontrar el agente
    async with sesion_db() as db:
        for agent_type in target_types:
            query = """
                SELECT system_prompt, name 
                FROM agents 
                WHERE tenant_id = :tid AND agent_type = :type AND status = 'is_active' 
                LIMIT 1
            """
            result = await db.execute(text(query), {"tid": tenant_id, "type": agent_type})
            agent = result.fetchone()
            
            if agent:
                return agent.system_prompt # Éxito: Devolvemos el prompt del agente especializado
        
        # Si no encuentra nada, retorna prompt por defecto
        return "Eres un asistente útil. Responde al usuario de manera amable."
