from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy import text
from database import sesion_db
from routers.auth_router import get_usuario_actual
from auth import PayloadToken

router = APIRouter(prefix="/api/v1/plans", tags=["plans"])

PLAN_DETAILS = {
    "free": {
        "id": "free",
        "name": "Gratis",
        "price_monthly": 0,
        "description": "Perfecto para probar",
        "max_agents": 1,
        "max_messages_month": 100,
        "max_whatsapp_instances": 1,
        "features": [
            "1 Agente de ventas",
            "100 mensajes/mes",
            "1 Instancia WhatsApp",
            "Base de conocimiento básica",
            "Soporte por email"
        ],
        "limits": {
            "analytics": False,
            "telegram": False,
            "web_chat": False,
            "voice": False,
            "white_label": False
        }
    },
    "basic": {
        "id": "basic",
        "name": "Básico",
        "price_monthly": 29,
        "description": "Para negocios pequeños",
        "max_agents": 2,
        "max_messages_month": 2000,
        "max_whatsapp_instances": 1,
        "features": [
            "2 Agentes de ventas",
            "2,000 mensajes/mes",
            "1 Instancia WhatsApp",
            "CRM básico",
            "Base de conocimiento completa",
            "Soporte prioritario"
        ],
        "limits": {
            "analytics": True,
            "telegram": False,
            "web_chat": False,
            "voice": False,
            "white_label": False
        }
    },
    "pro": {
        "id": "pro",
        "name": "Profesional",
        "price_monthly": 99,
        "description": "Para crecer",
        "max_agents": 5,
        "max_messages_month": 10000,
        "max_whatsapp_instances": 3,
        "features": [
            "5 Agentes de ventas",
            "10,000 mensajes/mes",
            "3 Instancias WhatsApp",
            "Telegram integrado",
            "Web Chat embebible",
            "CRM avanzado",
            "Analíticas detalladas",
            "Base de conocimiento ILIMITADA",
            "Soporte prioritario"
        ],
        "limits": {
            "analytics": True,
            "telegram": True,
            "web_chat": True,
            "voice": False,
            "white_label": False
        }
    },
    "enterprise": {
        "id": "enterprise",
        "name": "Empresarial",
        "price_monthly": 299,
        "description": "Para grandes empresas",
        "max_agents": -1,
        "max_messages_month": -1,
        "max_whatsapp_instances": -1,
        "features": [
            "Agentes ILIMITADOS",
            "Mensajes ILIMITADOS",
            "Instancias WhatsApp ILIMITADAS",
            "Telegram integrado",
            "Web Chat premium",
            "Voz (STT/TTS)",
            "White-label (dominio propio)",
            "API REST completa",
            "Analíticas avanzadas",
            "Soporte dedicado 24/7",
            "Training personalizado"
        ],
        "limits": {
            "analytics": True,
            "telegram": True,
            "web_chat": True,
            "voice": True,
            "white_label": True
        }
    }
}


class PlanDetails(BaseModel):
    id: str
    name: str
    price_monthly: int
    description: str
    max_agents: int
    max_messages_month: int
    max_whatsapp_instances: int
    features: List[str]
    limits: dict


class PlanComparison(BaseModel):
    id: str
    name: str
    price: int
    agents: int
    messages: int
    whatsapp: int
    analytics: bool
    telegram: bool
    web_chat: bool
    voice: bool
    white_label: bool


@router.get("", response_model=List[PlanDetails])
async def list_plans():
    """Listar todos los planes disponibles"""
    plans = []
    for plan_id, plan_data in PLAN_DETAILS.items():
        plans.append(PlanDetails(**plan_data))
    return plans


@router.get("/{plan_id}", response_model=PlanDetails)
async def get_plan(plan_id: str):
    """Obtener detalle de un plan específico"""
    if plan_id not in PLAN_DETAILS:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return PlanDetails(**PLAN_DETAILS[plan_id])


@router.get("/compare", response_model=List[PlanComparison])
async def compare_plans():
    """Comparar todos los planes"""
    comparison = []
    for plan_id, plan_data in PLAN_DETAILS.items():
        comparison.append(PlanComparison(
            id=plan_id,
            name=plan_data["name"],
            price=plan_data["price_monthly"],
            agents=plan_data["max_agents"],
            messages=plan_data["max_messages_month"],
            whatsapp=plan_data["max_whatsapp_instances"],
            **plan_data["limits"]
        ))
    return comparison


@router.get("/current")
async def get_current_plan(usuario: PayloadToken = Depends(get_usuario_actual)):
    """Obtener el plan actual del tenant autenticado"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        result = await db.execute(text("""
            SELECT plan, max_agents, max_messages_month, messages_used_month, status
            FROM tenants
            WHERE id = :tid
        """), {"tid": usuario.tenant_id})
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        plan_id = str(row[0]) if row[0] else "free"
        plan_data = PLAN_DETAILS.get(plan_id, PLAN_DETAILS["free"])
        
        # Calcular uso actual
        messages_used = int(row[3]) if row[3] else 0
        max_messages = int(row[2]) if row[2] else 100
        max_agents = int(row[1]) if row[1] else 1
        
        return {
            "current_plan": plan_id,
            "plan_name": plan_data["name"],
            "status": str(row[4]) if row[4] else "active",
            "limits": {
                "messages": {
                    "max": max_messages,
                    "used": messages_used,
                    "remaining": max(0, max_messages - messages_used),
                    "percentage": (messages_used / max_messages * 100) if max_messages > 0 else 0
                },
                "agents": {
                    "max": max_agents,
                    "used": await get_agents_count(db, usuario.tenant_id)
                },
                "whatsapp": {
                    "max": plan_data["max_whatsapp_instances"]
                }
            },
            "features": plan_data["features"],
            "upgrade_available": plan_id != "enterprise",
            "price_monthly": plan_data["price_monthly"]
        }


async def get_agents_count(db, tenant_id: str) -> int:
    """Obtener cantidad de agentes activos"""
    result = await db.execute(text("""
        SELECT COUNT(*) 
        FROM agents 
        WHERE tenant_id = :tid AND status = 'is_active'
    """), {"tid": tenant_id})
    
    count = result.scalar()
    return int(count) if count else 0


@router.get("/usage")
async def get_plan_usage(
    days: int = 30,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener estadísticas de uso del plan actual"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        # Obtener información del plan
        tenant_result = await db.execute(text("""
            SELECT plan, max_agents, max_messages_month
            FROM tenants
            WHERE id = :tid
        """), {"tid": usuario.tenant_id})
        
        tenant_row = tenant_result.fetchone()
        if not tenant_row:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        plan_id = str(tenant_row[0]) if tenant_row[0] else "free"
        max_agents = int(tenant_row[1]) if tenant_row[1] else 1
        max_messages = int(tenant_row[2]) if tenant_row[2] else 100
        
        # Obtener uso de mensajes
        messages_result = await db.execute(text("""
            SELECT COUNT(*) as messages_used
            FROM mensajes m
            JOIN conversaciones c ON m.conversation_id = c.id
            WHERE c.tenant_id = :tid
                AND m.created_at >= NOW() - INTERVAL ':days days'
        """), {"tid": usuario.tenant_id, "days": days})
        
        messages_row = messages_result.fetchone()
        messages_used = int(messages_row[0]) if messages_row else 0
        
        # Obtener uso de agentes
        agents_used = await get_agents_count(db, usuario.tenant_id)
        
        # Obtener uso de conversaciones
        conversations_result = await db.execute(text("""
            SELECT COUNT(*) as conversations_used
            FROM conversaciones
            WHERE tenant_id = :tid
                AND iniciada_en >= NOW() - INTERVAL ':days days'
        """), {"tid": usuario.tenant_id, "days": days})
        
        conversations_row = conversations_result.fetchone()
        conversations_used = int(conversations_row[0]) if conversations_row else 0
        
        plan_data = PLAN_DETAILS.get(plan_id, PLAN_DETAILS["free"])
        
        return {
            "plan": {
                "id": plan_id,
                "name": plan_data["name"],
                "price_monthly": plan_data["price_monthly"]
            },
            "period": {
                "days": days,
                "from_date": (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d"),
                "to_date": datetime.now().strftime("%Y-%m-%d")
            },
            "usage": {
                "agents": {
                    "used": agents_used,
                    "limit": max_agents,
                    "percentage": (agents_used / max_agents * 100) if max_agents > 0 else 0,
                    "status": "warning" if agents_used >= max_agents else "ok"
                },
                "messages": {
                    "used": messages_used,
                    "limit": max_messages,
                    "percentage": (messages_used / max_messages * 100) if max_messages > 0 else 0,
                    "status": "warning" if messages_used >= max_messages else "ok"
                },
                "conversations": conversations_used
            },
            "features_enabled": plan_data["limits"]
        }


@router.post("/calculate-price")
async def calculate_price(plan_id: str, quantity: int = 1):
    """Calcular price para un plan"""
    if plan_id not in PLAN_DETAILS:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    plan_data = PLAN_DETAILS[plan_id]
    monthly_price = plan_data["price_monthly"]
    
    # Descuentos por volumen
    if quantity >= 12:  # 1 año
        discount = 0.20  # 20% descuento
    elif quantity >= 6:  # 6 meses
        discount = 0.10  # 10% descuento
    elif quantity >= 3:  # 3 meses
        discount = 0.05  # 5% descuento
    else:
        discount = 0.0
    
    monthly_discounted = monthly_price * (1 - discount)
    total_price = monthly_discounted * quantity
    
    return {
        "plan": plan_id,
        "plan_name": plan_data["name"],
        "quantity": quantity,
        "monthly_price": monthly_price,
        "discount_percentage": discount * 100,
        "monthly_discounted": monthly_discounted,
        "total_price": total_price,
        "savings": (monthly_price - monthly_discounted) * quantity
    }
