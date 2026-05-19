from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime

from core.database import get_db_session as obtener_sesion
from auth import get_tenant_actual_opcional as get_tenant_actual
from database import configurar_rls

router = APIRouter(prefix="/api/v1/invoices", tags=["Billing"])

@router.get("")
async def list_invoices(
    tenant_id: UUID = Depends(get_tenant_actual),
    db: AsyncSession = Depends(obtener_sesion)
):
    await configurar_rls(db, tenant_id)
    
    query = text("""
        SELECT id, order_id, customer_id, status, amount as total_amount, metadata, created_at as issued_at
        FROM operational_invoices
        WHERE tenant_id = :tenant_id
        ORDER BY created_at DESC
        LIMIT 100
    """)
    result = await db.execute(query, {"tenant_id": str(tenant_id)})
    
    invoices = []
    for row in result.fetchall():
        invoices.append({
            "id": str(row.id),
            "order_id": str(row.order_id) if row.order_id else None,
            "customer_id": str(row.customer_id) if row.customer_id else None,
            "total_amount": float(row.total_amount) if row.total_amount else 0.0,
            "status": row.status,
            "issued_at": row.issued_at.isoformat() if row.issued_at else None,
            "metadata": row.metadata
        })
        
    return invoices

@router.post("/from-order/{order_id}")
async def generate_invoice_stub(
    order_id: str, 
    db: AsyncSession = Depends(obtener_sesion), 
    tenant_id: UUID = Depends(get_tenant_actual)
):
    """Crea registro de factura operativa con Snapshot Inmutable y Secuencia"""
    await configurar_rls(db, tenant_id)
    
    # 1. Traer datos completos para el snapshot (Order + Items)
    # En un sistema real esto requeriría un JOIN con order_items y catalog_items
    query = text("""
        SELECT id, customer_id, status, total_amount, currency
        FROM orders 
        WHERE id = :id AND tenant_id = :tenant_id
    """)
    result = await db.execute(query, {"id": order_id, "tenant_id": str(tenant_id)})
    order = result.fetchone()
    
    if not order:
        raise HTTPException(404, "Order not found")
        
    if order.status not in ('paid', 'shipped', 'delivered', 'completed'):
        raise HTTPException(400, "Order must be paid or fulfilled to generate operational receipt")
        
    # Check duplicate
    check_query = text("SELECT id FROM operational_invoices WHERE order_id = :order_id AND tenant_id = :tenant_id")
    check_result = await db.execute(check_query, {"order_id": order_id, "tenant_id": str(tenant_id)})
    if check_result.fetchone():
        raise HTTPException(400, "An operational receipt already exists for this order")
        
    # 2. Receipt Number Strategy (e.g., RC-2026-0001)
    # Fetch count to increment (in a real highly-concurrent system, use a PostgreSQL sequence per tenant)
    count_query = text("SELECT COUNT(id) FROM operational_invoices WHERE tenant_id = :tenant_id")
    count_result = await db.execute(count_query, {"tenant_id": str(tenant_id)})
    current_count = count_result.scalar() or 0
    receipt_number = f"RC-{datetime.utcnow().year}-{(current_count + 1):06d}"
    
    # 3. Construir Immutable Snapshot
    import json
    snapshot_data = {
        "company": {"name": "Tenant Business", "address": "123 Main St", "logo_url": ""},
        "customer": {"id": str(order.customer_id) if order.customer_id else None},
        "items": [], # Aquí irían los order_items reales congelados
        "pricing": {
            "total_amount": float(order.total_amount),
            "currency": order.currency or "USD"
        },
        "branding": {"theme": "dark", "accent_color": "#06b6d4"},
        "legal": {"disclaimer": "Documento Operacional - Sin Valor Tributario. La factura legal se emitirá previa validación de datos fiscales."}
    }
    
    # 4. Insertar Invoice
    insert_query = text("""
        INSERT INTO operational_invoices (
            tenant_id, order_id, customer_id, subtotal, total_amount, 
            status, receipt_number, snapshot_data, template_version, legal_disclaimer, issued_at
        )
        VALUES (
            :tenant_id, :order_id, :customer_id, :amount, :amount, 
            'generated', :receipt_number, :snapshot_data, 'v1', :disclaimer, NOW()
        )
        RETURNING id
    """)
    result = await db.execute(insert_query, {
        "tenant_id": str(tenant_id),
        "order_id": str(order.id),
        "customer_id": str(order.customer_id) if order.customer_id else None,
        "amount": order.total_amount,
        "receipt_number": receipt_number,
        "snapshot_data": json.dumps(snapshot_data),
        "disclaimer": snapshot_data["legal"]["disclaimer"]
    })
    invoice_id = result.scalar()
    
    # Commit
    await db.commit()
    
    return {
        "invoice_id": str(invoice_id), 
        "receipt_number": receipt_number,
        "status": "generated"
    }

@router.get("/{invoice_id}")
async def get_invoice(
    invoice_id: str,
    db: AsyncSession = Depends(obtener_sesion),
    tenant_id: UUID = Depends(get_tenant_actual)
):
    """Obtiene una factura operativa y su snapshot inmutable"""
    await configurar_rls(db, tenant_id)
    
    query = text("""
        SELECT id, order_id, receipt_number, status, total_amount, snapshot_data, issued_at
        FROM operational_invoices
        WHERE id = :id AND tenant_id = :tenant_id
    """)
    result = await db.execute(query, {"id": invoice_id, "tenant_id": str(tenant_id)})
    invoice = result.fetchone()
    
    if not invoice:
        raise HTTPException(404, "Receipt not found")
        
    return {
        "id": str(invoice.id),
        "order_id": str(invoice.order_id),
        "receipt_number": invoice.receipt_number,
        "status": invoice.status,
        "total_amount": float(invoice.total_amount) if invoice.total_amount else 0,
        "snapshot_data": invoice.snapshot_data,
        "issued_at": str(invoice.issued_at) if invoice.issued_at else None
    }
