-- ==========================================
-- FLUXAGENT V2 — PHASE 3C.1: ENTERPRISE INVENTORY INTELLIGENCE
-- Tablas: tenant_inventory_policies, inventory_ledger, inventory_snapshots
-- ==========================================

BEGIN;

-- 1. ELIMINAR OBJETOS ANTIGUOS SI EXISTEN
DROP TABLE IF EXISTS inventory_transactions CASCADE;
DROP TABLE IF EXISTS inventory_ledger CASCADE;
DROP TABLE IF EXISTS inventory_snapshots CASCADE;
DROP TABLE IF EXISTS tenant_inventory_policies CASCADE;

-- 2. TENANT INVENTORY POLICIES
-- Define reglas de negocio operacionales a nivel de empresa
CREATE TABLE IF NOT EXISTS tenant_inventory_policies (
    tenant_id UUID PRIMARY KEY,
    allow_backorders BOOLEAN DEFAULT FALSE,
    reservation_timeout_minutes INTEGER DEFAULT 15,
    negative_stock_allowed BOOLEAN DEFAULT FALSE,
    reconciliation_policy VARCHAR(50) DEFAULT 'LOCAL_WINS' CHECK (reconciliation_policy IN ('ERP_WINS', 'LOCAL_WINS', 'MERGE', 'MANUAL_REVIEW')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. INVENTORY LEDGER (Immutable, Append-Only)
-- La fuente absoluta de verdad del inventario.
CREATE TABLE IF NOT EXISTS inventory_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant_inventory_policies(tenant_id),
    catalog_item_id UUID NOT NULL,
    
    -- Correlation Tracing (CRITICO PARA AUDITORIA ENTERPRISE)
    correlation_id VARCHAR(255) NOT NULL, -- ej: txn_abc123 (ata el pago, la orden y el inventario)
    source_type VARCHAR(50) NOT NULL,     -- ej: 'checkout', 'webhook', 'sync_worker'
    source_id VARCHAR(255),               -- ej: ID del worker o de la sesión de stripe
    
    -- Tipo de Movimiento Estricto
    movement_type VARCHAR(50) NOT NULL CHECK (movement_type IN (
        'IMPORT', 'RESERVE', 'COMMIT', 'RELEASE', 
        'ADJUSTMENT', 'RETURN', 'REFUND', 'TRANSFER', 'SYNC_CORRECTION'
    )),
    
    reservation_type VARCHAR(20) CHECK (reservation_type IN ('soft', 'hard')), -- Soft: Carrito. Hard: Pagado pero no despachado.
    
    -- Razón Operacional
    reason_code VARCHAR(100) NOT NULL,
    
    -- Cantidad (+10, -2, etc.)
    quantity INTEGER NOT NULL,
    
    -- Metadatos
    metadata JSONB DEFAULT '{}'::jsonb,
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_inv_ledger_tenant_item ON inventory_ledger(tenant_id, catalog_item_id, created_at);
CREATE INDEX IF NOT EXISTS idx_inv_ledger_correlation ON inventory_ledger(correlation_id);

-- 4. INVENTORY SNAPSHOTS (Read-Optimized View)
-- Caché transaccional actualizada por el Engine, regenerable desde el Ledger.
CREATE TABLE IF NOT EXISTS inventory_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    catalog_item_id UUID NOT NULL,
    
    -- Concurrency Protection
    version_number INTEGER NOT NULL DEFAULT 1,
    
    -- Tres ejes de inventario
    current_stock INTEGER NOT NULL DEFAULT 0,  
    reserved_stock INTEGER NOT NULL DEFAULT 0, 
    available_stock INTEGER GENERATED ALWAYS AS (current_stock - reserved_stock) STORED, 
    
    last_ledger_id UUID REFERENCES inventory_ledger(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT unique_tenant_item_snapshot UNIQUE (tenant_id, catalog_item_id)
);

-- Note: No forzamos CHECK(available_stock >= 0) en DB porque `tenant_inventory_policies` 
-- podría permitir allow_backorders. Esa validación se hará estrictamente en Python.

CREATE INDEX IF NOT EXISTS idx_inv_snapshots_tenant ON inventory_snapshots(tenant_id);

-- ==========================================
-- RLS MULTI-TENANT
-- ==========================================
ALTER TABLE tenant_inventory_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE inventory_snapshots ENABLE ROW LEVEL SECURITY;

DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'tenant_inventory_policies', 'inventory_ledger','inventory_snapshots'
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
