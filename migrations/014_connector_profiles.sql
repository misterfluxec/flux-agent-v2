-- 014_connector_profiles.sql
-- Fase 2A: Infraestructura de Integración Desacoplada

-- 1. CONNECTOR PROFILES
-- Almacena la configuración, credenciales encriptadas y el mapeo semántico de un ERP.
CREATE TABLE IF NOT EXISTS connector_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL, -- ej: 'google_sheets', 'sqlserver', 'ms_graph'
    name VARCHAR(100) NOT NULL, -- ej: 'ERP Principal'
    
    -- Configuración técnica y credenciales (en la app debería encriptarse antes de guardar)
    config_encrypted JSONB NOT NULL DEFAULT '{}',
    
    -- Mapeo semántico (Connector -> Canonical Model)
    mapping_json JSONB NOT NULL DEFAULT '{}',
    
    -- Reglas de sincronización (frecuencia, merge vs overwrite, etc)
    sync_rules JSONB NOT NULL DEFAULT '{}',
    
    status VARCHAR(50) DEFAULT 'active', -- active, paused, error
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 2. SYNC JOBS
-- Telemetría operativa estricta para observabilidad y debugging.
CREATE TABLE IF NOT EXISTS sync_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    connector_profile_id UUID NOT NULL REFERENCES connector_profiles(id) ON DELETE CASCADE,
    
    entity_type VARCHAR(50) NOT NULL, -- customers, inventory, orders
    status VARCHAR(50) NOT NULL DEFAULT 'running', -- running, success, partial_error, failed
    
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    duration_ms INTEGER,
    
    rows_read INTEGER DEFAULT 0,
    rows_inserted INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    rows_skipped INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    
    -- Para auditoría de idempotencia
    checksum_changes INTEGER DEFAULT 0,
    trigger_source VARCHAR(50) DEFAULT 'manual', -- manual, schedule, webhook
    
    error_log JSONB, -- Detalles de los fallos
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. HABILITAR SEGURIDAD MULTI-TENANT (RLS)

ALTER TABLE connector_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sync_jobs ENABLE ROW LEVEL SECURITY;

-- Políticas para connector_profiles
CREATE POLICY tenant_isolation_connector_profiles ON connector_profiles
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

CREATE POLICY tenant_insert_connector_profiles ON connector_profiles
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

-- Políticas para sync_jobs
CREATE POLICY tenant_isolation_sync_jobs ON sync_jobs
    FOR ALL
    USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

CREATE POLICY tenant_insert_sync_jobs ON sync_jobs
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

-- 4. ÍNDICES DE RENDIMIENTO
CREATE INDEX idx_connector_profiles_tenant ON connector_profiles(tenant_id);
CREATE INDEX idx_sync_jobs_tenant ON sync_jobs(tenant_id);
CREATE INDEX idx_sync_jobs_profile ON sync_jobs(connector_profile_id);
CREATE INDEX idx_sync_jobs_status ON sync_jobs(status);
CREATE INDEX idx_sync_jobs_created ON sync_jobs(created_at DESC);
