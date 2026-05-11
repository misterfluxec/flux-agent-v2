from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from core.exceptions import BusinessRuleError, InsufficientStockError, SlotUnavailableError

# ==========================================
# INPUT SCHEMAS (Pydantic v2)
# ==========================================
class CheckAvailabilityInput(BaseModel):
    product_name_or_query: str = Field(description="Nombre o consulta del producto a buscar")
    quantity: int = Field(ge=1, default=1)
    preferred_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None

class QuoteItemInput(BaseModel):
    business_offer_id: str
    quantity: int = Field(ge=1, default=1)
    unit_price: float

class CreateQuoteInput(BaseModel):
    items: List[QuoteItemInput]
    valid_days: int = Field(ge=1, le=90, default=7)
    tax_rate: float = Field(ge=0.0, le=100.0, default=0.0)
    notes: str = ""
    customer_id: Optional[str] = None

class CreateOrderInput(BaseModel):
    quote_id: Optional[str] = None
    customer_id: Optional[str] = None
    items: Optional[List[QuoteItemInput]] = None
    payment_method: str = Field(default="pending")
    fulfillment_type: str = Field(default="pending")
    scheduled_for: Optional[datetime] = None

# ==========================================
# HANDLERS
# ==========================================
async def check_availability(
    input_data: CheckAvailabilityInput, 
    tenant_id: str, 
    db: AsyncSession
) -> Dict[str, Any]:
    
    query = text("""
        SELECT id, type, name, description, base_price, stock_quantity, is_active, sales_playbook, commercial_strategy
        FROM business_offers 
        WHERE tenant_id = :tenant_id 
        AND (name ILIKE :query OR description ILIKE :query)
        AND is_active = true
        LIMIT 3
    """)
    result = await db.execute(query, {
        "tenant_id": tenant_id,
        "query": f"%{input_data.product_name_or_query}%"
    })
    
    items = result.fetchall()
    if not items:
        raise BusinessRuleError(f"No encontré productos con el nombre: {input_data.product_name_or_query}")

    # Tomar el mejor match (el primero)
    item = items[0]
    
    result_dict = {
        "available": False, 
        "business_offer_id": str(item.id),
        "name": item.name,
        "item_type": item.type, 
        "details": {"base_price": float(item.base_price)},
        "yanua_revenue_intelligence": {
            "sales_playbook": item.sales_playbook if hasattr(item, 'sales_playbook') else {},
            "commercial_strategy": item.commercial_strategy if hasattr(item, 'commercial_strategy') else {}
        }
    }

    if item.type == "physical_product":
        result_dict["details"]["stock"] = item.stock_quantity
        result_dict["available"] = item.stock_quantity >= input_data.quantity
        if not result_dict["available"]:
            raise InsufficientStockError(f"Stock insuficiente para {item.name}. Solicitado: {input_data.quantity}, Disponible: {item.stock_quantity}")

    elif item.type in ("booking", "appointment", "service"):
        # Lógica simplificada de slots para el ejemplo
        result_dict["available"] = True
        result_dict["details"]["next_available_slot"] = (datetime.utcnow() + timedelta(days=1)).isoformat()
    else:
        result_dict["available"] = True  # digital/subscription/custom

    return result_dict

async def create_quote(
    input_data: CreateQuoteInput,
    tenant_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    subtotal = 0.0
    for spec in input_data.items:
        subtotal += spec.quantity * spec.unit_price

    tax_amt = subtotal * (input_data.tax_rate / 100)
    total = subtotal + tax_amt

    import secrets
    public_view_token = secrets.token_urlsafe(32)

    quote_query = text("""
        INSERT INTO quotes (tenant_id, customer_id, status, subtotal, total, valid_until, public_view_token)
        VALUES (:tenant_id, :customer_id, 'draft', :subtotal, :total, NOW() + INTERVAL '7 days', :token)
        RETURNING id
    """)
    quote_result = await db.execute(quote_query, {
        "tenant_id": tenant_id,
        "customer_id": input_data.customer_id if input_data.customer_id else None,
        "subtotal": subtotal,
        "total": total,
        "token": public_view_token
    })
    quote_id = quote_result.scalar_one()

    for item in input_data.items:
        await db.execute(text("""
            INSERT INTO quote_items (tenant_id, quote_id, business_offer_id, quantity, unit_price)
            VALUES (:tenant_id, :quote_id, :business_offer_id, :quantity, :unit_price)
        """), {
            "tenant_id": tenant_id,
            "quote_id": quote_id,
            "business_offer_id": item.business_offer_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        })

    return {
        "quote_id": str(quote_id),
        "status": "draft",
        "total": round(float(total), 2),
        "public_url": f"/quotes/view/{public_view_token}"
    }

async def create_order(
    input_data: CreateOrderInput,
    tenant_id: str,
    db: AsyncSession
) -> Dict[str, Any]:
    
    subtotal = 0.0
    order_items_data = []

    if input_data.quote_id:
        # TODO: Fetch quote from DB to calculate
        raise NotImplementedError("Resolución desde quote no implementada en este stub")
    else:
        if not input_data.items: 
            raise BusinessRuleError("Se requieren ítems si no hay quote_id")
        
        for i in input_data.items:
            subtotal += i.unit_price * i.quantity
            order_items_data.append(i)

    order_query = text("""
        INSERT INTO orders (tenant_id, quote_id, customer_id, status, subtotal, total_amount, payment_method)
        VALUES (:tenant_id, :quote_id, :customer_id, 'pending', :subtotal, :subtotal, :payment_method)
        RETURNING id
    """)
    order_result = await db.execute(order_query, {
        "tenant_id": tenant_id,
        "quote_id": input_data.quote_id,
        "customer_id": input_data.customer_id,
        "subtotal": subtotal,
        "payment_method": input_data.payment_method
    })
    order_id = order_result.scalar_one()

    for item in order_items_data:
        await db.execute(text("""
            INSERT INTO order_items (tenant_id, order_id, business_offer_id, quantity, unit_price)
            VALUES (:tenant_id, :order_id, :business_offer_id, :quantity, :unit_price)
        """), {
            "tenant_id": tenant_id,
            "order_id": order_id,
            "business_offer_id": item.business_offer_id,
            "quantity": item.quantity,
            "unit_price": item.unit_price
        })

        # Descontar stock
        await db.execute(text("""
            UPDATE business_offers 
            SET stock_quantity = stock_quantity - :qty
            WHERE id = :catalog_id AND type = 'physical_product'
        """), {
            "qty": item.quantity,
            "catalog_id": item.business_offer_id
        })

    return {
        "order_id": str(order_id),
        "status": "pending",
        "total": round(float(subtotal), 2)
    }
