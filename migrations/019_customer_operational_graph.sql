-- ==========================================
-- FLUXAGENT V2 — PHASE 3E: CUSTOMER OPERATIONAL GRAPH
-- Tablas: customer_timeline_events
-- ==========================================

BEGIN;

-- 1. CUSTOMER TIMELINE EVENTS (The Business Memory Layer)
-- Agrega eventos de múltiples dominios (Quotes, Orders, Payments, Inventory, Support) 
-- en un solo historial cronológico por cliente.
CREATE TABLE IF NOT EXISTS customer_timeline_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    customer_id UUID NOT NULL REFERENCES customers(id),
    
    -- Categorización del Evento
    event_category VARCHAR(50) NOT NULL CHECK (event_category IN (
        'commerce', 'payment', 'inventory', 'communication', 'support', 'ai_interaction'
    )),
    event_type VARCHAR(100) NOT NULL, -- ej: 'order.created', 'payment.failed', 'quote.viewed'
    
    -- Grafo de relaciones (Opcionales, para navegación)
    order_id UUID,
    quote_id UUID,
    payment_intent_id UUID,
    
    -- Trazabilidad con el Outbox / Domain Event original
    source_event_id VARCHAR(255), 
    
    -- Datos semánticos para el humano y la IA (Evita hacer JOINs complejos al leer)
    title VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Nivel de severidad operacional (útil para que la IA priorice atención)
    severity VARCHAR(20) DEFAULT 'info' CHECK (severity IN ('info', 'success', 'warning', 'critical')),
    
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices Críticos para el Feed del Cliente
CREATE INDEX IF NOT EXISTS idx_cust_timeline_customer ON customer_timeline_events(tenant_id, customer_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_cust_timeline_severity ON customer_timeline_events(tenant_id, customer_id, severity) WHERE severity IN ('warning', 'critical');

-- ==========================================
-- RLS MULTI-TENANT
-- ==========================================
ALTER TABLE customer_timeline_events ENABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'customer_timeline_events' LOOP
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
