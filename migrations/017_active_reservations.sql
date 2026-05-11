-- ==========================================
-- FLUXAGENT V2 — PHASE 3C.2: RESERVATION ENGINE
-- Tablas: active_reservations
-- ==========================================

BEGIN;

-- 1. ACTIVE RESERVATIONS
-- Rastreador de estado para las reservas del Ledger. 
-- Permite al Expiration Worker barrer eficientemente las reservas caducadas sin escanear todo el Ledger.
CREATE TABLE IF NOT EXISTS active_reservations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant_inventory_policies(tenant_id),
    catalog_item_id UUID NOT NULL,
    
    correlation_id VARCHAR(255) NOT NULL, -- Atado a la transacción original (ej: ID del carrito)
    ledger_id UUID NOT NULL REFERENCES inventory_ledger(id), -- Puntero al asiento de RESERVE en el Ledger
    
    reservation_type VARCHAR(20) NOT NULL CHECK (reservation_type IN ('soft', 'hard')), 
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'committed', 'released')),
    
    expires_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices Críticos para el Expiration Worker
CREATE INDEX IF NOT EXISTS idx_active_res_expiration ON active_reservations(tenant_id, status, expires_at) WHERE status = 'active';
CREATE INDEX IF NOT EXISTS idx_active_res_correlation ON active_reservations(correlation_id);

-- ==========================================
-- RLS MULTI-TENANT
-- ==========================================
ALTER TABLE active_reservations ENABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename = 'active_reservations' LOOP
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
