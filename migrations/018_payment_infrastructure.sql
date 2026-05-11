-- ==========================================
-- FLUXAGENT V2 — PHASE 3D: PAYMENT INFRASTRUCTURE
-- Tablas: payment_intents, webhook_events
-- ==========================================

BEGIN;

-- 1. PAYMENT INTENTS
-- Registra cada intento de pago. Una orden puede tener múltiples intentos si los primeros fallan.
CREATE TABLE IF NOT EXISTS payment_intents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    order_id UUID NOT NULL REFERENCES orders(id),
    
    external_provider VARCHAR(50) NOT NULL, -- ej: 'mercadopago', 'stripe'
    external_transaction_id VARCHAR(255),   -- ID generado por el proveedor
    
    amount DECIMAL(15, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    
    status VARCHAR(50) NOT NULL CHECK (status IN (
        'pending', 'authorized', 'processing', 'paid', 
        'failed', 'expired', 'chargeback', 'refunded', 'cancelled'
    )),
    
    idempotency_key VARCHAR(255) NOT NULL,  -- Generado por FluxAgent para enviar al proveedor
    
    metadata JSONB DEFAULT '{}'::jsonb,
    error_details TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_tenant_idempotency UNIQUE (tenant_id, idempotency_key)
);

CREATE INDEX IF NOT EXISTS idx_payment_intents_order ON payment_intents(order_id);
CREATE INDEX IF NOT EXISTS idx_payment_intents_external ON payment_intents(external_transaction_id) WHERE external_transaction_id IS NOT NULL;

-- 2. WEBHOOK EVENTS (Idempotency & Replay)
-- Almacena el webhook CRU que entra desde el proveedor antes de procesarlo.
-- Esto permite procesar asíncronamente y garantiza que un evento duplicado (mismo event_id de MP) sea ignorado.
CREATE TABLE IF NOT EXISTS webhook_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    
    provider VARCHAR(50) NOT NULL,
    provider_event_id VARCHAR(255) NOT NULL, -- ID del evento enviado por MercadoPago
    event_type VARCHAR(100) NOT NULL,        -- ej: 'payment.updated'
    
    payload JSONB NOT NULL,
    
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed', 'ignored')),
    error_message TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    
    CONSTRAINT unique_provider_event UNIQUE (provider, provider_event_id)
);

CREATE INDEX IF NOT EXISTS idx_webhook_events_pending ON webhook_events(status) WHERE status = 'pending';

-- ==========================================
-- RLS MULTI-TENANT
-- ==========================================
ALTER TABLE payment_intents ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_events ENABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'payment_intents', 'webhook_events'
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
