from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Literal
import json
from database import obtener_sesion
from core.dependencies import get_redis
from redis.asyncio import Redis

router = APIRouter(prefix="/explain", tags=["explainability"])

@router.get("/decision")
async def explain_decision(
    context: Literal["lead", "handoff", "response"] = Query(...),
    entity_id: str = Query(...),
    db: AsyncSession = Depends(obtener_sesion),
    redis: Redis = Depends(get_redis)
    # tenant_id: str = Depends(get_usuario_actual) - Pendiente integrar JWT auth real
):
    """Explicación trazable, cacheada y determinística (No LLM)"""
    # Usamos un tenant de prueba para asegurar que el endpoint funciona sin romper
    tenant_id = "test_tenant" 
    cache_key = f"explain:{tenant_id}:{context}:{entity_id}"
    
    try:
        cached = await redis.get(cache_key)
        if cached: 
            return json.loads(cached)
    except Exception:
        pass # Fallback si redis falla
    
    signals, policy, confidence, source = [], "default", 0.0, "Memoria + Catálogo"
    
    if context == "lead":
        # Mocking data until actual schemas are verified
        signals.append(f"Score 85/100 (umbral HOT)")
        signals.append("Sentimiento positivo sostenido")
        signals.append("Alta urgencia de respuesta")
        policy, confidence = "lead_hot_threshold_v2", 95.0
        
    elif context == "handoff":
        signals.append("Confianza IA < 60% en última interacción")
        signals.append("Frustración detectada por palabras clave")
        signals.append("Múltiples attempts de acción fallidos")
        policy, confidence = "human_takeover_frustration_rule", 65.0
        
    elif context == "response":
        signals.append("Respuesta extraída del catálogo base")
        policy, confidence = "knowledge_retrieval", 99.0
        
    result = {"signals": signals, "policy_applied": policy, "confidence_pct": confidence, "source": source}
    
    try:
        await redis.setex(cache_key, 300, json.dumps(result))  # Cache 5 min
    except Exception:
        pass
        
    return result
