from typing import Optional, Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

# ==========================================
# 1. CUSTOMERS
# ==========================================
class CustomerCreate(BaseModel):
    external_id: Optional[str] = None
    erp_customer_code: Optional[str] = None
    source_connector_id: Optional[str] = None
    
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    tax_id: Optional[str] = None
    
    lifecycle_stage: str = "lead"
    preferred_channel: Optional[str] = None
    
    billing_address: Optional[dict[str, Any]] = None
    shipping_address: Optional[dict[str, Any]] = None
    currency: str = "USD"
    metadata: dict[str, Any] = Field(default_factory=dict)

class CustomerResponse(CustomerCreate):
    id: UUID
    tenant_id: UUID
    churn_score: float
    ltv: float
    created_at: datetime
    updated_at: datetime

# ==========================================
# 2. PAYMENTS
# ==========================================
class PaymentCreate(BaseModel):
    order_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    
    provider: str
    provider_payment_id: Optional[str] = None
    provider_reference: Optional[str] = None
    
    amount: float
    currency: str = "USD"
    fee_amount: float = 0.0
    installments: int = 1
    
    status: str = "pending"
    payment_method: Optional[str] = None
    raw_payload: Optional[dict[str, Any]] = None
    correlation_id: Optional[UUID] = None

class PaymentResponse(PaymentCreate):
    id: UUID
    tenant_id: UUID
    net_amount: float
    approved_at: Optional[datetime] = None
    failed_reason: Optional[str] = None
    reconciled_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

# ==========================================
# 3. OPERATIONAL INVOICES
# ==========================================
class InvoiceCreate(BaseModel):
    order_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    payment_id: Optional[UUID] = None
    
    invoice_number: Optional[str] = None
    series: Optional[str] = None
    due_at: Optional[datetime] = None
    
    subtotal: float
    tax_amount: float = 0.0
    discount_amount: float = 0.0
    total_amount: float
    currency: str = "USD"
    
    status: str = "draft"
    metadata: dict[str, Any] = Field(default_factory=dict)

class InvoiceResponse(InvoiceCreate):
    id: UUID
    tenant_id: UUID
    issued_at: datetime
    pdf_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

# ==========================================
# 4. TENANT SUBSCRIPTIONS
# ==========================================
class TenantSubscriptionCreate(BaseModel):
    plan_id: Optional[UUID] = None
    status: str = "trial"
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    auto_renew: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)

class TenantSubscriptionResponse(TenantSubscriptionCreate):
    id: UUID
    tenant_id: UUID
    canceled_at: Optional[datetime] = None
    last_payment_id: Optional[UUID] = None
    next_billing_date: Optional[datetime] = None
    dunning_attempts: int = 0
    created_at: datetime
    updated_at: datetime

# ==========================================
# 5. INVENTORY TRANSACTIONS
# ==========================================
class InventoryTransactionCreate(BaseModel):
    product_id: UUID
    type: str
    quantity: int
    source: Optional[str] = None
    correlation_id: Optional[UUID] = None
    stock_before: Optional[int] = None
    stock_after: Optional[int] = None
    notes: Optional[str] = None

class InventoryTransactionResponse(InventoryTransactionCreate):
    id: UUID
    tenant_id: UUID
    created_at: datetime
