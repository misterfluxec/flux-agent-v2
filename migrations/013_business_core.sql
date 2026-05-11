-- ==========================================
-- FLUXAGENT V2 — PHASE 1: BUSINESS CORE
-- Tablas: customers, payments, operational_invoices, tenant_subscriptions, inventory_transactions
-- ==========================================

BEGIN;

-- 1. CUSTOMERS: Business Entity Master (ERP-Ready)
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    -- Identidad ERP / Conectores
    external_id VARCHAR(255),  -- ID en sistema externo (SQL Server, Odoo, etc.)
    erp_customer_code VARCHAR(50),
    source_connector_id VARCHAR(50), -- 'sqlserver', 'woocommerce', 'manual'
    
    -- Datos Personales
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(255),
    phone VARCHAR(50),
    tax_id VARCHAR(50), -- RUT, CUIT, RFC
    
    -- Inteligencia Comercial
    lifecycle_stage VARCHAR(20) DEFAULT 'lead' CHECK (lifecycle_stage IN ('lead', 'qualified', 'customer', 'churned', 'vip')),
    churn_score FLOAT DEFAULT 0.0 CHECK (churn_score BETWEEN 0.0 AND 1.0),
    ltv DECIMAL(10,2) DEFAULT 0.00,
    preferred_channel VARCHAR(20), -- 'whatsapp', 'email', 'web'
    
    -- Dirección / Billing
    billing_address JSONB,
    shipping_address JSONB,
    currency VARCHAR(3) DEFAULT 'USD',
    
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, email),
    UNIQUE(tenant_id, phone)
);

CREATE INDEX IF NOT EXISTS idx_customers_tenant_external ON customers(tenant_id, external_id) WHERE external_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_customers_lifecycle ON customers(tenant_id, lifecycle_stage);

-- 2. PAYMENTS: Ledger Financiero & Conciliación
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    order_id UUID, -- Referencia a orders (opcional si es pago suelto)
    customer_id UUID,
    
    -- Proveedor
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('mercadopago', 'stripe', 'manual', 'transfer')),
    provider_payment_id VARCHAR(255),
    provider_reference VARCHAR(255),
    
    -- Montos & Moneda
    amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    fee_amount DECIMAL(10,2) DEFAULT 0.00,
    net_amount DECIMAL(10,2) GENERATED ALWAYS AS (amount - fee_amount) STORED,
    installments INTEGER DEFAULT 1, -- Cuotas
    
    -- Estado & Conciliación
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'authorized', 'captured', 'failed', 'refunded')),
    payment_method VARCHAR(50), -- 'credit_card', 'debit', 'pix', 'cash'
    approved_at TIMESTAMPTZ,
    failed_reason VARCHAR(255),
    
    -- Webhook & Trazabilidad
    raw_payload JSONB, -- Payload crudo del webhook para auditoría
    correlation_id UUID, -- Para tracing distribuido
    reconciled_at TIMESTAMPTZ,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_payments_tenant_status ON payments(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_payments_provider_ref ON payments(provider_payment_id) WHERE provider_payment_id IS NOT NULL;

-- 3. OPERATIONAL INVOICES: Documentos Legales Simples
CREATE TABLE IF NOT EXISTS operational_invoices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    order_id UUID,
    customer_id UUID,
    payment_id UUID,
    
    -- Numeración
    invoice_number VARCHAR(50) UNIQUE,
    series VARCHAR(20),
    issued_at TIMESTAMPTZ DEFAULT NOW(),
    due_at TIMESTAMPTZ,
    
    -- Montos
    subtotal DECIMAL(10,2) NOT NULL,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Estado & PDF
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    pdf_url TEXT,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_invoices_tenant_status ON operational_invoices(tenant_id, status);

-- 4. TENANT SUBSCRIPTIONS: SaaS Billing (FluxAgent)
-- Separado de las suscripciones que el cliente venda a sus usuarios.
CREATE TABLE IF NOT EXISTS tenant_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL UNIQUE,
    plan_id UUID,
    
    -- Ciclos
    status VARCHAR(20) DEFAULT 'trial' CHECK (status IN ('trial', 'active', 'past_due', 'cancelled', 'expired')),
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    trial_end TIMESTAMPTZ,
    canceled_at TIMESTAMPTZ,
    
    -- Pago
    last_payment_id UUID,
    next_billing_date TIMESTAMPTZ,
    auto_renew BOOLEAN DEFAULT true,
    dunning_attempts INTEGER DEFAULT 0,
    
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_subs_status ON tenant_subscriptions(status);

-- 5. INVENTORY TRANSACTIONS: Auditoría de Stock
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    product_id UUID,
    
    -- Movimiento
    type VARCHAR(20) NOT NULL CHECK (type IN ('sale', 'purchase', 'return', 'adjustment', 'reservation')),
    quantity INTEGER NOT NULL,
    source VARCHAR(50), -- 'order_123', 'manual_adj', 'connector_sync'
    correlation_id UUID,
    
    -- Snapshot
    stock_before INTEGER,
    stock_after INTEGER,
    
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inv_trans_product ON inventory_transactions(product_id, created_at);

-- ==========================================
-- RLS: Aislamiento Multi-Tenant Estricto
-- ==========================================
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE operational_invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_transactions ENABLE ROW LEVEL SECURITY;

-- Políticas (Asumiendo app.current_tenant_id configurado en sesión)
DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'customers','payments','operational_invoices','tenant_subscriptions','inventory_transactions'
    ) LOOP
        BEGIN
            EXECUTE format('CREATE POLICY %I_tenant_isolation ON %I USING (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
            EXECUTE format('CREATE POLICY %I_tenant_insert ON %I FOR INSERT WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
            EXECUTE format('CREATE POLICY %I_tenant_update ON %I FOR UPDATE USING (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
            EXECUTE format('CREATE POLICY %I_tenant_delete ON %I FOR DELETE USING (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END;
    END LOOP;
END $$;

COMMIT;
