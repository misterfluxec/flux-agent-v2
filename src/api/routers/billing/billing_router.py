from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy import text
from datetime import datetime
from database import sesion_db
from auth import get_usuario_actual
from auth import PayloadToken
from core.plan_manager import PlanManager

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


class BillingInfo(BaseModel):
    company_name: str
    tax_id: str  # RFC/NIF
    address: str
    email: str
    city: str
    zip_code: str
    country: str = "Ecuador"


class InvoiceResponse(BaseModel):
    id: str
    tenant_id: str
    invoice_number: str
    date: str
    due_date: str
    amount: float
    status: str
    description: str


class SubscriptionResponse(BaseModel):
    plan: str
    status: str
    current_period_start: str
    current_period_end: str
    max_agents: int
    max_messages_month: int
    price: float


@router.post("/info")
async def save_billing_info(
    info: BillingInfo,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Guardar información de facturación"""
    async with sesion_db() as db:
        # Configurar RLS para el tenant
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        result = await db.execute(text("""
            UPDATE tenants
            SET billing_info = :billing_info::jsonb, updated_at = NOW()
            WHERE id = :tid
            RETURNING id
        """), {
            "tid": usuario.tenant_id,
            "billing_info": info.model_dump_json()
        })
        
        if not result.fetchone():
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        await db.commit()
    
    return {"message": "Información de facturación guardada correctamente"}


@router.get("/info")
async def get_billing_info(usuario: PayloadToken = Depends(get_usuario_actual)):
    """Obtener información de facturación"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        result = await db.execute(text("""
            SELECT billing_info
            FROM tenants
            WHERE id = :tid
        """), {"tid": usuario.tenant_id})
        
        row = result.fetchone()
        
        if not row or not row[0]:
            return BillingInfo(
                company_name="",
                tax_id="",
                address="",
                email="",
                city="",
                zip_code="",
                country="Ecuador"
            )
        
        return row[0]


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(usuario: PayloadToken = Depends(get_usuario_actual)):
    """Obtener suscripción actual"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        result = await db.execute(text("""
            SELECT plan, status, contract_start as contract_start, contract_end as contract_end, 
                   max_agents, max_messages_month as max_messages_month, 0 as price
            FROM tenants
            WHERE id = :tid
        """), {"tid": usuario.tenant_id})
        
        row = result.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Suscripción no encontrada")
        
        plan_prices = {"free": 0, "basic": 29, "pro": 99, "enterprise": 299}
        
        return SubscriptionResponse(
            plan=str(row[0]) if row[0] else "free",
            status=str(row[1]) if row[1] else "active",
            current_period_start=str(row[2]) if row[2] else "",
            current_period_end=str(row[3]) if row[3] else "",
            max_agents=int(row[4]) if row[4] else 1,
            max_messages_month=int(row[5]) if row[5] else 100,
            price=plan_prices.get(str(row[0]), 0)
        )


@router.get("/invoices", response_model=List[InvoiceResponse])
async def list_invoices(usuario: PayloadToken = Depends(get_usuario_actual)):
    """Listar facturas"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        # Verificar si existe la tabla invoices
        table_check = await db.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'invoices'
            )
        """))
        
        if not table_check.scalar():
            return []
        
        result = await db.execute(text("""
            SELECT id, tenant_id, invoice_number, date, due_date, amount, status, description
            FROM invoices
            WHERE tenant_id = :tid
            ORDER BY date DESC
            LIMIT 20
        """), {"tid": usuario.tenant_id})
        
        invoices = []
        for row in result:
            invoices.append(InvoiceResponse(
                id=str(row[0]),
                tenant_id=str(row[1]),
                invoice_number=str(row[2]),
                date=str(row[3]) if row[3] else "",
                due_date=str(row[4]) if row[4] else "",
                amount=float(row[5]) if row[5] else 0.0,
                status=str(row[6]),
                description=str(row[7])
            ))
    
    return invoices


@router.get("/history")
async def get_billing_history(
    days: int = 30,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener historial de facturación"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        result = await db.execute(text("""
            SELECT 
                DATE(iniciada_en) as month,
                COUNT(*) as conversations,
                COALESCE(SUM(valor_venta), 0) as revenue
            FROM conversaciones
            WHERE tenant_id = CAST(:tid AS UUID)
                AND iniciada_en >= NOW() - INTERVAL '1 day' * :days
            GROUP BY DATE(iniciada_en)
            ORDER BY month DESC
            LIMIT 12
        """), {"tid": usuario.tenant_id, "days": days})
        
        history = []
        for row in result:
            history.append({
                "month": str(row[0]) if row[0] else "",
                "conversations": int(row[1]) if row[1] else 0,
                "revenue": float(row[2]) if row[2] else 0.0
            })
    
    return history


@router.post("/upgrade")
async def upgrade_plan(
    new_plan: str,
    request: Request,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Mejorar plan de suscripción"""
    # PlanManager para obtener límites y precios desde DB/Redis
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        manager = PlanManager(redis=request.app.state.redis, db=db)
        try:
            features = await manager.get_plan(new_plan)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
        
        await db.execute(text("""
            UPDATE tenants
            SET plan = :plan, 
                max_agents = :max_agents,
                max_messages_month = :max_messages,
                price = :price,
                updated_at = NOW()
            WHERE id = :tid
        """), {
            "tid": usuario.tenant_id,
            "plan": new_plan,
            "max_agents": features.max_agents,
            "max_messages": features.max_messages_month,
            "price": features.price_usd
        })
        await db.commit()
    
    return {
        "message": f"Plan mejorado a {new_plan}", 
        "plan": new_plan,
        "price": features.price_usd
    }


@router.get("/usage")
async def get_usage_stats(
    days: int = 30,
    usuario: PayloadToken = Depends(get_usuario_actual)
):
    """Obtener estadísticas de uso"""
    async with sesion_db() as db:
        await db.execute(text(f"SET app.current_tenant_id = '{usuario.tenant_id}'"))
        
        # Obtener límites del plan
        tenant_result = await db.execute(text("""
            SELECT max_agents, max_messages_month, plan
            FROM tenants
            WHERE id = :tid
        """), {"tid": usuario.tenant_id})
        
        tenant_row = tenant_result.fetchone()
        if not tenant_row:
            raise HTTPException(status_code=404, detail="Tenant no encontrado")
        
        max_agents = int(tenant_row[0]) if tenant_row[0] else 1
        max_messages = int(tenant_row[1]) if tenant_row[1] else 100
        current_plan = str(tenant_row[2]) if tenant_row[2] else "free"
        
        # Obtener uso actual de agentes
        agents_result = await db.execute(text("""
            SELECT COUNT(*) FROM agents 
            WHERE tenant_id = CAST(:tid AS UUID)
        """), {"tid": usuario.tenant_id})
        agents_used = int(agents_result.scalar() or 0)

        # Obtener uso actual de conversaciones
        convs_result = await db.execute(text("""
            SELECT COUNT(*) FROM conversaciones 
            WHERE tenant_id = CAST(:tid AS UUID)
              AND iniciada_en >= NOW() - INTERVAL '1 day' * :days
        """), {"tid": usuario.tenant_id, "days": days})
        conversations_used = int(convs_result.scalar() or 0)

        # Obtener uso actual de mensajes
        messages_result = await db.execute(text("""
            SELECT COUNT(*) FROM mensajes m
            JOIN conversaciones c ON m.conversacion_id = c.id
            WHERE c.tenant_id = CAST(:tid AS UUID)
              AND m.creado_en >= NOW() - INTERVAL '1 day' * :days
        """), {"tid": usuario.tenant_id, "days": days})
        messages_used = int(messages_result.scalar() or 0)
        
        return {
            "plan": current_plan,
            "period_days": days,
            "agents": {
                "used": agents_used,
                "limit": max_agents,
                "percentage": (agents_used / max_agents * 100) if max_agents > 0 else 0
            },
            "messages": {
                "used": messages_used,
                "limit": max_messages,
                "percentage": (messages_used / max_messages * 100) if max_messages > 0 else 0
            },
            "conversations": conversations_used
        }
