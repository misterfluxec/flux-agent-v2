from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import text
from database import sesion_db
from auth import get_usuario_actual
from auth import PayloadToken
from core.db.helpers import interval_days

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


class AnalyticsOverview(BaseModel):
    total_conversations: int
    total_messages: int
    total_sales: float
    conversion_rate: float
    avg_response_time: float
    sentiment_score: float


class DailyStats(BaseModel):
    date: str
    conversations: int
    messages: int
    sales: float
    leads: int


class AgentStats(BaseModel):
    agent_id: str
    agent_name: str
    conversations: int
    messages: int
    sales: float
    avg_response_time: float


@router.get("/overview", response_model=AnalyticsOverview)
async def get_analytics_overview(
    days: int = 7,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener overview de analytics para el tenant actual"""
    try:
        async with sesion_db() as db:
            # Configurar RLS para el tenant
            await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
            
            # Obtener conversaciones y ventas
            result = await db.execute(text(f"""
                SELECT 
                    COUNT(*) as total_conversations,
                    COALESCE(SUM(valor_venta), 0) as total_sales,
                    COUNT(CASE WHEN venta_cerrada = true THEN 1 END) as closed_sales
                FROM conversaciones
                WHERE tenant_id = :tid
                    AND iniciada_en >= NOW() - {interval_days('days')}
            """), {"tid": usuario.tenant_id, "days": days})
            
            row = result.fetchone()
            
            total_conversations = int(row[0]) if row[0] else 0
            total_sales = float(row[1]) if row[1] else 0.0
            closed_sales = int(row[2]) if row[2] else 0
            
            # Obtener mensajes
            result2 = await db.execute(text(f"""
                SELECT COUNT(*)
                FROM mensajes
                WHERE tenant_id = :tid
                    AND created_at >= NOW() - {interval_days('days')}
            """), {"tid": usuario.tenant_id, "days": days})
            
            row_messages = await result2.fetchone()
            total_messages = int(row_messages[0]) if row_messages and row_messages[0] else 0
            
            # Calcular tasa de conversión
            conversion_rate = (closed_sales / total_conversations * 100) if total_conversations > 0 else 0.0
            
            # Obtener sentimiento promedio
            result3 = await db.execute(text(f"""
                SELECT COALESCE(AVG(sentimiento), 0) as avg_sentiment
                FROM conversaciones
                WHERE tenant_id = :tid
                    AND sentimiento IS NOT NULL
                    AND iniciada_en >= NOW() - {interval_days('days')}
            """), {"tid": usuario.tenant_id, "days": days})
            
            sentiment_row = result3.fetchone()
            sentiment_score = float(sentiment_row[0]) if sentiment_row and sentiment_row[0] else 0.0
            
            # Calcular tiempo de respuesta promedio
            avg_response_time = 0.0  # TODO: Implementar cálculo real basado en timestamps de mensajes
            
            return AnalyticsOverview(
                total_conversations=total_conversations,
                total_messages=total_messages,
                total_sales=total_sales,
                conversion_rate=conversion_rate,
                avg_response_time=avg_response_time,
                sentiment_score=sentiment_score
            )
            
    except Exception as e:
        print(f"Analytics error: {e}")
        return AnalyticsOverview(
            total_conversations=0,
            total_messages=0,
            total_sales=0.0,
            conversion_rate=0.0,
            avg_response_time=0.0,
            sentiment_score=0.0
        )


@router.get("/daily", response_model=List[DailyStats])
async def get_daily_stats(
    days: int = 7,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener estadísticas diarias"""
    try:
        async with sesion_db() as db:
            await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
            
            result = await db.execute(text("""
                SELECT 
                    DATE(iniciada_en) as date,
                    COUNT(*) as conversations,
                    COALESCE(SUM(valor_venta), 0) as sales,
                    COUNT(CASE WHEN lead_calificado = true THEN 1 END) as leads
                FROM conversaciones
                WHERE tenant_id = :tid
                    AND iniciada_en >= NOW() - INTERVAL ':days days'
                GROUP BY DATE(iniciada_en)
                ORDER BY date DESC
            """), {"tid": usuario.tenant_id, "days": days})
            
            daily_stats = []
            for row in result:
                # Obtener mensajes del día
                msg_result = await db.execute(text("""
                    SELECT COUNT(*)
                    FROM mensajes
                    WHERE tenant_id = :tid
                        AND DATE(created_at) = :date
                """), {"tid": usuario.tenant_id, "date": row[0]})
                
                messages_count = int(msg_result.fetchone()[0]) if msg_result.fetchone() else 0
                
                daily_stats.append(DailyStats(
                    date=str(row[0]),
                    conversations=int(row[1]) if row[1] else 0,
                    messages=messages_count,
                    sales=float(row[2]) if row[2] else 0.0,
                    leads=int(row[3]) if row[3] else 0
                ))
            
            return daily_stats
            
    except Exception as e:
        print(f"Daily stats error: {e}")
        return []


@router.get("/agents", response_model=List[AgentStats])
async def get_agent_stats(usuario: PayloadToken = Depends(get_usuario_actual)):
    """Obtener estadísticas por agente"""
    try:
        async with sesion_db() as db:
            await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
            
            result = await db.execute(text("""
                SELECT 
                    a.id,
                    a.name,
                    COUNT(c.id) as conversations,
                    COALESCE(SUM(c.valor_venta), 0) as sales,
                    COALESCE(AVG(c.sentimiento), 0) as avg_sentiment
                FROM agents a
                LEFT JOIN conversaciones c ON c.agent_id = a.id
                WHERE a.tenant_id = :tid
                GROUP BY a.id, a.name
                ORDER BY conversations DESC
            """), {"tid": usuario.tenant_id})
            
            stats = []
            for row in result:
                # Obtener mensajes por agente
                msg_result = await db.execute(text("""
                    SELECT COUNT(*)
                    FROM mensajes m
                    JOIN conversaciones c ON m.conversation_id = c.id
                    WHERE c.agent_id = :agent_id
                        AND c.tenant_id = :tid
                """), {"agent_id": row[0], "tid": usuario.tenant_id})
                
                messages_count = int(msg_result.fetchone()[0]) if msg_result.fetchone() else 0
                
                stats.append(AgentStats(
                    agent_id=str(row[0]),
                    agent_name=str(row[1]),
                    conversations=int(row[2]) if row[2] else 0,
                    messages=messages_count,
                    sales=float(row[3]) if row[3] else 0.0,
                    avg_response_time=0.0  # TODO: Implementar cálculo real
                ))
            
            return stats
            
    except Exception as e:
        print(f"Agent stats error: {e}")
        return []


@router.get("/sentiment")
async def get_sentiment_analysis(
    days: int = 7,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener análisis de sentimiento"""
    try:
        async with sesion_db() as db:
            await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
            
            result = await db.execute(text("""
                SELECT 
                    CASE 
                        WHEN sentimiento > 0.3 THEN 'satisfecho'
                        WHEN sentimiento < -0.3 THEN 'frustrado'
                        ELSE 'neutral'
                    END as sentiment_category,
                    COUNT(*) as count
                FROM conversaciones
                WHERE tenant_id = :tid
                    AND sentimiento IS NOT NULL
                    AND iniciada_en >= NOW() - INTERVAL ':days days'
                GROUP BY sentiment_category
            """), {"tid": usuario.tenant_id, "days": days})
            
            sentiment_data = {"satisfecho": 0, "neutral": 0, "frustrado": 0}
            
            for row in result:
                sentiment_data[row[0]] = int(row[1]) if row[1] else 0
            
            return sentiment_data
            
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return {"satisfecho": 0, "neutral": 0, "frustrado": 0}


@router.get("/kpis")
async def get_kpis(
    days: int = 30,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener KPIs principales"""
    try:
        async with sesion_db() as db:
            await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
            
            result = await db.execute(text("""
                SELECT 
                    COUNT(*) as conversations,
                    COUNT(CASE WHEN lead_calificado = true THEN 1 END) as leads,
                    COUNT(CASE WHEN venta_cerrada = true THEN 1 END) as sales,
                    COALESCE(SUM(valor_venta), 0) as revenue,
                    COALESCE(AVG(valor_venta), 0) as avg_ticket
                FROM conversaciones
                WHERE tenant_id = :tid
                    AND iniciada_en >= NOW() - INTERVAL ':days days'
            """), {"tid": usuario.tenant_id, "days": days})
            
            row = result.fetchone()
            
            conversations = int(row[0]) if row[0] else 0
            leads = int(row[1]) if row[1] else 0
            sales = int(row[2]) if row[2] else 0
            revenue = float(row[3]) if row[3] else 0.0
            avg_ticket = float(row[4]) if row[4] else 0.0
            
            conversion_rate = (sales / conversations * 100) if conversations > 0 else 0.0
            
            return {
                "revenue": revenue,
                "conversations": conversations,
                "leads": leads,
                "sales": sales,
                "conversion_rate": conversion_rate,
                "avg_ticket": avg_ticket
            }
            
    except Exception as e:
        print(f"KPIs error: {e}")
        return {
            "revenue": 0.0,
            "conversations": 0,
            "leads": 0,
            "sales": 0,
            "conversion_rate": 0.0,
            "avg_ticket": 0.0
        }
