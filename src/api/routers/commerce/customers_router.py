from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List
from uuid import UUID

from database import obtener_sesion
from auth import get_tenant_actual_opcional as get_tenant_actual
from database import configurar_rls
from services.customer_intelligence_engine import CustomerIntelligenceEngine

router = APIRouter(prefix="/api/v1/customers", tags=["Customer Intelligence"])

@router.get("", summary="Directorio Inteligente de Clientes")
async def get_customers(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
) -> List[Dict[str, Any]]:
    """Devuelve la lista unificada de Master Data con métricas agregadas."""
    await configurar_rls(db, tenant_id)
    
    query = """
        SELECT 
            c.id, c.first_name, c.last_name, c.email, c.phone, 
            c.lifecycle_stage,
            m.ltv, m.order_count, m.churn_score, m.health_state, m.last_purchase_at
        FROM customers c
        LEFT JOIN customer_metrics m ON c.id = m.customer_id AND c.tenant_id = m.tenant_id
        WHERE c.tenant_id = :tid
        ORDER BY c.created_at DESC
        LIMIT 100
    """
    
    result = await db.execute(text(query), {"tid": str(tenant_id)})
    rows = result.fetchall()
    
    customers = []
    for r in rows:
        customers.append({
            "id": str(r.id),
            "name": f"{r.first_name or ''} {r.last_name or ''}".strip() or "Sin Nombre",
            "email": r.email,
            "phone": r.phone,
            "lifecycle_stage": r.lifecycle_stage,
            "metrics": {
                "ltv": float(r.ltv) if r.ltv else 0.0,
                "order_count": r.order_count or 0,
                "churn_score": float(r.churn_score) if r.churn_score else 0.0,
                "health_state": r.health_state or "healthy",
                "last_purchase_at": r.last_purchase_at.isoformat() if r.last_purchase_at else None
            }
        })
    return customers

@router.get("/{customer_id}", summary="Customer Master Data")
async def get_customer_master_data(
    customer_id: str,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
) -> Dict[str, Any]:
    """Recupera el perfil 360 del cliente incluyendo Identidades, Métricas y Preferencias"""
    await configurar_rls(db, tenant_id)
    
    q_customer = text("SELECT * FROM customers WHERE id = :id AND tenant_id = :tid")
    res_cust = await db.execute(q_customer, {"id": customer_id, "tid": str(tenant_id)})
    cust = res_cust.fetchone()
    
    if not cust:
        raise HTTPException(404, "Customer not found")
        
    q_metrics = text("SELECT * FROM customer_metrics WHERE customer_id = :id")
    res_metrics = await db.execute(q_metrics, {"id": customer_id})
    metrics = res_metrics.fetchone()
    
    q_prefs = text("SELECT * FROM customer_preferences WHERE customer_id = :id")
    res_prefs = await db.execute(q_prefs, {"id": customer_id})
    prefs = res_prefs.fetchone()
    
    return {
        "id": str(cust.id),
        "first_name": cust.first_name,
        "last_name": cust.last_name,
        "email": cust.email,
        "phone": cust.phone,
        "lifecycle_stage": cust.lifecycle_stage,
        "metrics": {
            "ltv": float(metrics.ltv) if metrics else 0.0,
            "order_count": metrics.order_count if metrics else 0,
            "churn_score": float(metrics.churn_score) if metrics else 0.0,
            "health_state": metrics.health_state if metrics else "healthy",
        },
        "preferences": {
            "accepts_marketing": prefs.accepts_marketing if prefs else True,
            "accepts_whatsapp": prefs.accepts_whatsapp if prefs else True,
            "global_opt_out": prefs.global_opt_out if prefs else False
        }
    }

@router.get("/{customer_id}/timeline", summary="Activity Stream")
async def get_customer_timeline(
    customer_id: str,
    limit: int = 50,
    offset: int = 0,
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    """Devuelve el historial inmutable de actividades operacionales."""
    await configurar_rls(db, tenant_id)
    engine = CustomerIntelligenceEngine(db, str(tenant_id))
    events = await engine.get_customer_timeline(customer_id, limit, offset)
    return {"events": events}
