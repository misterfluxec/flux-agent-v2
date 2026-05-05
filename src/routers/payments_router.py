# =============================================================================
# FLUXAGENT V2 — ROUTER DE PAGOS Y FACTURACIÓN
# =============================================================================
# Integración con Mercado Pago para pagos recurrentes
# Gestión de facturas, suscripciones y cupones
# =============================================================================

import logging
import uuid
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import httpx

from auth import PayloadToken, get_usuario_actual, get_tenant_actual, solo_admin
from database import obtener_sesion, configurar_rls
from config import obtener_config

logger = logging.getLogger(__name__)
config = obtener_config()

router = APIRouter(prefix="/api/v1/payments", tags=["Pagos y Facturación"])


# =============================================================================
# SCHEMAS
# =============================================================================

class CreateSubscriptionRequest(BaseModel):
    plan_id: str
    payment_method: str = "mercadopago"
    card_token: Optional[str] = None


class SubscriptionResponse(BaseModel):
    id: str
    tenant_id: str
    plan: str
    estado: str
    monto: float
    moneda: str
    periodo: str
    fecha_inicio: str
    fecha_proxima_renovacion: str


class InvoiceResponse(BaseModel):
    id: str
    tenant_id: str
    subscription_id: str
    numero: str
    fecha_emision: str
    fecha_vencimiento: str
    monto: float
    estado: str
    pdf_url: Optional[str] = None


class CouponRequest(BaseModel):
    codigo: str
    tipo_descuento: str  # "porcentaje" | "fijo"
    valor: float
    valido_hasta: str
    uso_maximo: int = 1
    plan_aplicable: Optional[str] = None


# =============================================================================
# GET /api/v1/payments/subscription — Obtener suscripción actual
# =============================================================================

@router.get("/subscription", summary="Obtiene la suscripción actual del tenant")
async def get_subscription(
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Retorna los detalles de la suscripción activa del tenant."""
    await configurar_rls(db, uuid.UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("""
            SELECT id, plan, estado, monto, moneda, periodo, fecha_inicio, fecha_proxima_renovacion
            FROM subscriptions
            WHERE tenant_id = :tid AND estado = 'activa'
            ORDER BY fecha_inicio DESC
            LIMIT 1
        """),
        {"tid": usuario.tenant_id}
    )
    
    row = result.fetchone()
    if not row:
        return {
            "suscripcion": None,
            "plan": usuario.plan,
            "mensaje": "No hay suscripción activa"
        }
    
    return {
        "suscripcion": {
            "id": str(row.id),
            "plan": row.plan,
            "estado": row.estado,
            "monto": float(row.monto),
            "moneda": row.moneda,
            "periodo": row.periodo,
            "fecha_inicio": str(row.fecha_inicio),
            "fecha_proxima_renovacion": str(row.fecha_proxima_renovacion),
        }
    }


# =============================================================================
# POST /api/v1/payments/subscription — Crear/actualizar suscripción
# =============================================================================

@router.post("/subscription", summary="Crea una nueva suscripción", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    datos: CreateSubscriptionRequest,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """
    Crea una nueva suscripción con Mercado Pago.
    Por ahora es una simulación - en producción se conectaría a MP API.
    """
    await configurar_rls(db, uuid.UUID(usuario.tenant_id))
    
    PLANES = {
        "starter": {"monto": 0, "moneda": "USD", "periodo": "mensual"},
        "pro": {"monto": 49, "moneda": "USD", "periodo": "mensual"},
        "enterprise": {"monto": 199, "moneda": "USD", "periodo": "mensual"},
    }
    
    plan_info = PLANES.get(datos.plan_id, PLANES["starter"])
    
    subscription_id = uuid4()
    fecha_inicio = datetime.now()
    fecha_renovacion = fecha_inicio + timedelta(days=30)
    
    await db.execute(
        text("""
            INSERT INTO subscriptions (
                id, tenant_id, plan, estado, monto, moneda, periodo,
                fecha_inicio, fecha_proxima_renovacion, external_subscription_id
            ) VALUES (
                :id, :tid, :plan, 'activa', :monto, :moneda, :periodo,
                :inicio, :renovacion, :external_id
            )
        """),
        {
            "id": str(subscription_id),
            "tid": usuario.tenant_id,
            "plan": datos.plan_id,
            "monto": plan_info["monto"],
            "moneda": plan_info["moneda"],
            "periodo": plan_info["periodo"],
            "inicio": fecha_inicio,
            "renovacion": fecha_renovacion,
            "external_id": f"mp_{subscription_id.hex[:12]}",
        }
    )
    
    await db.commit()
    
    logger.info(f"Suscripción creada: tenant={usuario.tenant_id}, plan={datos.plan_id}")
    
    return {
        "mensaje": "Suscripción creada correctamente",
        "subscription_id": str(subscription_id),
        "plan": datos.plan_id,
        "monto": plan_info["monto"],
        "moneda": plan_info["moneda"],
        "fecha_proxima_renovacion": str(fecha_renovacion),
    }


# =============================================================================
# GET /api/v1/payments/invoices — Lista de facturas
# =============================================================================

@router.get("/invoices", summary="Lista las facturas del tenant")
async def list_invoices(
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Retorna el historial de facturas del tenant."""
    await configurar_rls(db, uuid.UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("""
            SELECT id, numero, fecha_emision, fecha_vencimiento, monto, estado
            FROM invoices
            WHERE tenant_id = :tid
            ORDER BY fecha_emision DESC
            LIMIT 20
        """),
        {"tid": usuario.tenant_id}
    )
    
    invoices = []
    for row in result.fetchall():
        invoices.append({
            "id": str(row.id),
            "numero": row.numero,
            "fecha_emision": str(row.fecha_emision),
            "fecha_vencimiento": str(row.fecha_vencimiento),
            "monto": float(row.monto),
            "estado": row.estado,
        })
    
    return {"facturas": invoices}


# =============================================================================
# GET /api/v1/payments/invoices/{invoice_id} — Descargar factura
# =============================================================================

@router.get("/invoices/{invoice_id}/download", summary="Descargar factura PDF")
async def download_invoice(
    invoice_id: str,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Genera y retorna la URL de descarga de la factura PDF."""
    await configurar_rls(db, uuid.UUID(usuario.tenant_id))
    
    result = await db.execute(
        text("SELECT numero, monto, fecha_emision FROM invoices WHERE id = :id AND tenant_id = :tid"),
        {"id": invoice_id, "tid": usuario.tenant_id}
    )
    
    if not result.fetchone():
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    return {
        "pdf_url": f"/api/v1/payments/invoices/{invoice_id}/pdf",
        "mensaje": "URL de descarga de factura PDF (simulado)"
    }


# =============================================================================
# POST /api/v1/payments/coupons — Crear cupón (solo Super Admin)
# =============================================================================

@router.post("/coupons", summary="Crea un cupón de descuento", status_code=status.HTTP_201_CREATED)
async def create_coupon(
    datos: CouponRequest,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Crea un nuevo cupón de descuento (solo para Super Admin)."""
    if usuario.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Solo Super Admin puede crear cupones")
    
    coupon_id = uuid4()
    
    await db.execute(
        text("""
            INSERT INTO coupons (id, codigo, tipo_descuento, valor, valido_hasta, uso_maximo, uso_actual, plan_aplicable)
            VALUES (:id, :codigo, :tipo, :valor, :valido, :maximo, 0, :plan)
        """),
        {
            "id": str(coupon_id),
            "codigo": datos.codigo.upper().strip(),
            "tipo": datos.tipo_descuento,
            "valor": datos.valor,
            "valido": datos.valido_hasta,
            "maximo": datos.uso_maximo,
            "plan": datos.plan_aplicable,
        }
    )
    await db.commit()
    
    return {
        "mensaje": "Cupón creado correctamente",
        "coupon_id": str(coupon_id),
        "codigo": datos.codigo.upper(),
    }


# =============================================================================
# POST /api/v1/payments/coupons/validate — Validar cupón
# =============================================================================

@router.post("/coupons/validate", summary="Valida un cupón de descuento")
async def validate_coupon(
    datos: dict,
    usuario: PayloadToken = Depends(get_usuario_actual),
    db: AsyncSession = Depends(obtener_sesion),
):
    """Valida un código de cupón y retorna el descuento aplicable."""
    codigo = datos.get("codigo", "").upper().strip()
    plan = datos.get("plan", "starter")
    
    result = await db.execute(
        text("""
            SELECT id, tipo_descuento, valor, uso_maximo, uso_actual, valido_hasta, plan_aplicable
            FROM coupons
            WHERE codigo = :codigo
        """),
        {"codigo": codigo}
    )
    
    coupon = result.fetchone()
    if not coupon:
        raise HTTPException(status_code=404, detail="Cupón no encontrado")
    
    if coupon.uso_actual >= coupon.uso_maximo:
        raise HTTPException(status_code=400, detail="Cupón alcanzado su límite de uso")
    
    if datetime.now() > coupon.valido_hasta:
        raise HTTPException(status_code=400, detail="Cupón ha expirado")
    
    if coupon.plan_aplicable and coupon.plan_aplicable != plan:
        raise HTTPException(status_code=400, detail="Cupón no aplicable a este plan")
    
    return {
        "valido": True,
        "tipo_descuento": coupon.tipo_descuento,
        "valor": float(coupon.valor),
        "coupon_id": str(coupon.id),
    }


# =============================================================================
# WEBHOOK DE MERCADO PAGO (para pagos automáticos)
# =============================================================================

@router.post("/webhook/mercadopago", summary="Webhook de Mercado Pago")
async def mercadopago_webhook(
    request: dict,
    background_tasks: BackgroundTasks,
):
    """
    Receives payment notifications from Mercado Pago.
    Updates subscription status based on payment results.
    """
    try:
        topic = request.get("topic")
        resource_id = request.get("resource_id")
        
        logger.info(f"MP Webhook: topic={topic}, resource={resource_id}")
        
        if topic == "payment":
            background_tasks.add_task(procesar_pago_mp, resource_id)
        
        return {"received": True}
    except Exception as e:
        logger.error(f"Error en webhook MP: {e}")
        return {"error": str(e)}


async def procesar_pago_mp(payment_id: str):
    """Procesa un pago de Mercado Pago en background."""
    logger.info(f"Procesando pago MP: {payment_id}")
    # Aquí iría la lógica real de procesamiento con la API de MP
    pass