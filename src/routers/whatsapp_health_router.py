"""
WHATSAPP HEALTH ENDPOINTS
=========================
API para verificar salud del número de WhatsApp.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any
from uuid import UUID

from database import obtener_sesion
from auth import get_usuario_actual, PayloadToken
from services.whatsapp_guardian import WhatsAppBanProtector

router = APIRouter(prefix="/api/v1/whatsapp", tags=["WhatsApp Health"])


@router.get("/health")
async def get_whatsapp_health(
    db: AsyncSession = Depends(obtener_sesion),
    usuario: PayloadToken = Depends(get_usuario_actual)
) -> Dict[str, Any]:
    """
    Retorna el estado de salud del número de WhatsApp del tenant.
    """
    tenant_id = UUID(usuario.tenant_id)
    
    # Obtener métricas de la base de datos
    res = await db.execute(text("""
        SELECT 
            quality_rating,
            conversations_today,
            conversations_limit,
            delivery_rate,
            error_count_today,
            blocks_last_24h,
            last_checked_at
        FROM whatsapp_health
        WHERE tenant_id = :tenant_id
    """), {"tenant_id": str(tenant_id)})
    
    row = res.fetchone()
    
    if not row:
        return {
            "status": "no_data",
            "quality_rating": "UNKNOWN",
            "conversations_today": 0,
            "conversations_limit": 1000,
            "delivery_rate": 100.0,
            "message": "No hay datos de WhatsApp. Configura tu número primero."
        }
    
    # Calcular estado
    if row.quality_rating == "RED" or row.error_count_today > 10:
        status = "critical"
    elif row.quality_rating == "YELLOW" or row.error_count_today > 5:
        status = "degraded"
    else:
        status = "healthy"
    
    return {
        "status": status,
        "quality_rating": row.quality_rating,
        "conversations_today": row.conversations_today,
        "conversations_limit": row.conversations_limit,
        "conversations_remaining": max(0, row.conversations_limit - row.conversations_today),
        "delivery_rate": float(row.delivery_rate) if row.delivery_rate else 100.0,
        "error_count_today": row.error_count_today,
        "blocks_last_24h": row.blocks_last_24h,
        "last_checked_at": row.last_checked_at.isoformat() if row.last_checked_at else None,
        "recommendation": _get_recommendation(row)
    }


@router.get("/health/detailed")
async def get_whatsapp_health_detailed(
    db: AsyncSession = Depends(obtener_sesion),
    usuario: PayloadToken = Depends(get_usuario_actual)
) -> Dict[str, Any]:
    """
    Retorna métricas detalladas de uso de WhatsApp.
    """
    tenant_id = UUID(usuario.tenant_id)
    
    # Usage stats del mes actual
    res = await db.execute(text("""
        SELECT 
            COUNT(*) as total_conversations,
            SUM(message_count) as total_messages,
            SUM(CASE WHEN channel_used = 'evolution' THEN 1 ELSE 0 END) as evolution_count,
            SUM(CASE WHEN channel_used = 'cloud_api' THEN 1 ELSE 0 END) as cloud_count,
            SUM(total_cost_usd) as total_cost,
            SUM(CASE WHEN conversation_type = 'marketing' THEN 1 ELSE 0 END) as marketing_count
        FROM whatsapp_usage
        WHERE tenant_id = :tenant_id 
        AND first_message_at >= date_trunc('month', CURRENT_DATE)
    """), {"tenant_id": str(tenant_id)})
    
    row = res.fetchone()
    
    return {
        "this_month": {
            "total_conversations": row.total_conversations or 0,
            "total_messages": row.total_messages or 0,
            "evolution_api_usage": row.evolution_count or 0,
            "cloud_api_usage": row.cloud_count or 0,
            "marketing_messages": row.marketing_count or 0,
            "estimated_cost_usd": float(row.total_cost or 0)
        }
    }


def _get_recommendation(row) -> str:
    """Genera recomendación según el estado."""
    if row[0] == "RED" or (row[4] and row[4] > 10):
        return "CRÍTICO: Tu número está en riesgo. Detén mensajes de marketing inmediatamente y espera 48h."
    elif row[0] == "YELLOW" or (row[4] and row[4] > 5):
        return "Precaución: Reduce mensajes de marketing. Evita palabras spam y速率 límites."
    elif row[2] and row[2] >= row[3] * 0.9:
        return "Advertencia: Estás cerca del límite diario de conversaciones."
    else:
        return "Número en buen estado. Continúa operación normal."


@router.post("/health/refresh")
async def refresh_whatsapp_health(
    db: AsyncSession = Depends(obtener_sesion),
    usuario: PayloadToken = Depends(get_usuario_actual)
) -> Dict[str, Any]:
    """
    Fuerza actualización de métricas de salud.
    """
    tenant_id = UUID(usuario.tenant_id)
    
    # Obtener protector y calcular salud
    protector = WhatsAppBanProtector()
    health = await protector.get_health_status(str(tenant_id))
    
    # Actualizar base de datos
    await db.execute(text("""
        INSERT INTO whatsapp_health (tenant_id, quality_rating, last_checked_at)
        VALUES (:tenant_id, :quality, NOW())
        ON CONFLICT (tenant_id) DO UPDATE SET
            quality_rating = :quality,
            last_checked_at = NOW(),
            updated_at = NOW()
    """), {
        "tenant_id": str(tenant_id),
        "quality": health.get("quality_rating", "UNKNOWN")
    })
    
    await db.commit()
    
    return {"status": "refreshed", "health": health}