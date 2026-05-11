-- ==========================================
-- FLUXAGENT V2 — MIGRATION 012: ERP CONNECTORS
-- ==========================================
-- Tabla para almacenar configuraciones de conexión a ERPs externos.
-- Las credenciales se guardan encriptadas (EncryptionService).
-- RLS habilitado para aislamiento multi-tenant.
-- ==========================================

BEGIN;

CREATE TABLE IF NOT EXISTS erp_connections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    connector_type VARCHAR(30) NOT NULL CHECK (connector_type IN ('sqlserver', 'odoo', 'sap_b1', 'siigo', 'softland', 'custom')),
    name VARCHAR(255) NOT NULL,
    connection_string_encrypted TEXT NOT NULL,
    schema_name VARCHAR(100) DEFAULT 'dbo',
    field_mapping JSONB DEFAULT '{}'::jsonb,
    sync_frequency VARCHAR(20) DEFAULT 'daily' CHECK (sync_frequency IN ('hourly', 'daily', 'weekly', 'manual')),
    status VARCHAR(20) DEFAULT 'configured' CHECK (status IN ('configured', 'connected', 'syncing', 'error', 'disabled')),
    last_synced_at TIMESTAMPTZ,
    sync_error_message TEXT,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_tenant_connector_name UNIQUE (tenant_id, name)
);

-- Índices de rendimiento
CREATE INDEX IF NOT EXISTS idx_erp_connections_tenant ON erp_connections(tenant_id);
CREATE INDEX IF NOT EXISTS idx_erp_connections_status ON erp_connections(tenant_id, status);

-- Log de sincronizaciones (historial de cada sync ejecutado)
CREATE TABLE IF NOT EXISTS erp_sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    connection_id UUID REFERENCES erp_connections(id) ON DELETE CASCADE,
    entity_type VARCHAR(30) NOT NULL,  -- 'product', 'inventory', 'customer', 'order'
    direction VARCHAR(10) DEFAULT 'import',
    total_fetched INTEGER DEFAULT 0,
    inserted INTEGER DEFAULT 0,
    updated INTEGER DEFAULT 0,
    skipped INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    error_details JSONB DEFAULT '[]'::jsonb,
    duration_ms INTEGER DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_erp_sync_logs_conn ON erp_sync_logs(connection_id, started_at DESC);

-- RLS: Aislamiento multi-tenant
ALTER TABLE erp_connections ENABLE ROW LEVEL SECURITY;
ALTER TABLE erp_sync_logs ENABLE ROW LEVEL SECURITY;

DO $$
DECLARE
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'erp_connections', 'erp_sync_logs'
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

-- Añadir columna external_id indexada a catalog_items para mapeo ERP
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'catalog_items' AND column_name = 'external_id'
    ) THEN
        ALTER TABLE catalog_items ADD COLUMN external_id VARCHAR(255);
        CREATE INDEX IF NOT EXISTS idx_catalog_items_external ON catalog_items(tenant_id, external_id);
    END IF;
END $$;

COMMIT;
