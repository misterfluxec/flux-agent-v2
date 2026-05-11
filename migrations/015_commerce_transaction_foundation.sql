-- ==========================================
-- FLUXAGENT V2 — PHASE 3A: COMMERCE TRANSACTION FOUNDATION
-- Tablas: event_outbox, operational_audit_log, inventory_locks
-- State Machines: quotes, orders, payments
-- ==========================================

BEGIN;

-- 1. EVENT OUTBOX PATTERN
-- Garantiza que los eventos se emitan incluso si Redis cae (Transacción DB -> Outbox -> Dispatcher)
CREATE TABLE IF NOT EXISTS event_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL, -- ej: order.created
    aggregate_id VARCHAR(255) NOT NULL, -- ej: ID de la orden
    aggregate_type VARCHAR(50) NOT NULL, -- ej: order
    payload JSONB NOT NULL,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'dispatched', 'failed')),
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    dispatched_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_event_outbox_pending ON event_outbox(tenant_id, status) WHERE status = 'pending';

-- 2. OPERATIONAL AUDIT LOG
-- Registro inmutable de cada acción crítica para Enterprise Trust y Compliance
CREATE TABLE IF NOT EXISTS operational_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    action VARCHAR(100) NOT NULL, -- ej: inventory.reserved, payment.reconciled
    actor_type VARCHAR(50) NOT NULL CHECK (actor_type IN ('human', 'system', 'connector', 'webhook', 'ai')),
    actor_id VARCHAR(255), -- User ID, Connector ID, etc.
    target_resource VARCHAR(100), -- order, customer, etc.
    target_id VARCHAR(255),
    changes JSONB, -- { "before": {...}, "after": {...} }
    metadata JSONB DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_tenant_target ON operational_audit_log(tenant_id, target_resource, target_id);

-- 3. INVENTORY LOCKS (Optimistic Locking & Reservations)
CREATE TABLE IF NOT EXISTS inventory_locks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    catalog_item_id UUID NOT NULL,
    order_id UUID, -- Opcional, puede estar bloqueado por un carrito abandonado temporal
    quote_id UUID,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    status VARCHAR(20) DEFAULT 'reserved' CHECK (status IN ('reserved', 'allocated', 'deducted', 'released')),
    expires_at TIMESTAMPTZ NOT NULL, -- Timeout para liberar reservas estancadas
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inv_locks_tenant_item ON inventory_locks(tenant_id, catalog_item_id, status);
CREATE INDEX IF NOT EXISTS idx_inv_locks_expiration ON inventory_locks(status, expires_at) WHERE status = 'reserved';

-- ==========================================
-- STRICT STATE MACHINES ENFORCEMENT
-- Actualización de constraints V1 a los estándares estrictos de Fase 3
-- ==========================================

-- 4. QUOTES STATE MACHINE
ALTER TABLE quotes DROP CONSTRAINT IF EXISTS quotes_status_check;
ALTER TABLE quotes ADD CONSTRAINT quotes_status_check 
CHECK (status IN ('draft', 'sent', 'viewed', 'accepted', 'expired', 'rejected', 'converted'));

-- 5. ORDERS STATE MACHINE
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_status_check 
CHECK (status IN ('pending', 'confirmed', 'processing', 'fulfilled', 'cancelled', 'refunded'));

-- 6. PAYMENTS STATE MACHINE (En tabla orders y payments)
ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_payment_status_check;
ALTER TABLE orders ADD CONSTRAINT orders_payment_status_check 
CHECK (payment_status IN ('pending', 'authorized', 'processing', 'paid', 'failed', 'expired', 'chargeback', 'refunded'));

ALTER TABLE payments DROP CONSTRAINT IF EXISTS payments_status_check;
ALTER TABLE payments ADD CONSTRAINT payments_status_check 
CHECK (status IN ('pending', 'authorized', 'processing', 'paid', 'failed', 'expired', 'chargeback', 'refunded'));

-- ==========================================
-- RLS MULTI-TENANT
-- ==========================================
ALTER TABLE event_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE operational_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_locks ENABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'event_outbox','operational_audit_log','inventory_locks'
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
