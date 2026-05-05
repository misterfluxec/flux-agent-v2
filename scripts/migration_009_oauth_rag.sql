-- migration_009_oauth_rag_sync.sql
-- Ejecutar en PostgreSQL con psql
-- Agrega capacidades de OAuth2 y Sincronización RAG desde Google Sheets/Excel Online

-- 1. Tabla para cuentas conectadas (Google, Microsoft, Yahoo)
CREATE TABLE IF NOT EXISTS connected_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Proveedor de identidad
    provider VARCHAR(20) NOT NULL CHECK (provider IN ('google', 'microsoft', 'yahoo')),
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255) NOT NULL,
    
    -- Tokens OAuth2 (CIFRADOS)
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    
    -- Scopes concedidos
    granted_scopes TEXT[],
    
    -- Metadata del proveedor
    provider_metadata JSONB DEFAULT '{}',
    
    -- Estado
    is_active BOOLEAN DEFAULT TRUE,
    last_synced_at TIMESTAMPTZ,
    sync_error_message TEXT,
    
    -- Auditoría
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ DEFAULT NOW(),
    
    -- Único por tenant + provider + provider_user_id
    UNIQUE(tenant_id, provider, provider_user_id)
);

CREATE INDEX IF NOT EXISTS idx_connected_accounts_tenant ON connected_accounts(tenant_id, is_active);
CREATE INDEX IF NOT EXISTS idx_connected_accounts_provider ON connected_accounts(provider, provider_user_id);

-- 2. Tabla para fuentes de datos sincronizadas
CREATE TABLE IF NOT EXISTS synced_sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    account_id UUID NOT NULL REFERENCES connected_accounts(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE, -- Vínculo al agente de confianza
    
    -- Identificación de la fuente
    source_type VARCHAR(20) NOT NULL CHECK (source_type IN ('google_sheets', 'excel_online', 'csv_url')),
    source_id VARCHAR(255) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT,
    
    -- Mapeo de columnas
    column_mapping JSONB NOT NULL,
    
    -- Configuración de sincronización
    sync_frequency VARCHAR(20) DEFAULT 'daily' CHECK (sync_frequency IN ('hourly', 'daily', 'weekly', 'webhook', 'manual')),
    last_synced_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('pending', 'syncing', 'success', 'failed')),
    
    -- Métricas
    rows_processed INTEGER DEFAULT 0,
    rows_added INTEGER DEFAULT 0,
    rows_updated INTEGER DEFAULT 0,
    rows_deleted INTEGER DEFAULT 0,
    
    -- Metadata extensible
    metadata JSONB DEFAULT '{}',
    
    -- Auditoría
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, source_type, source_id)
);

CREATE INDEX IF NOT EXISTS idx_synced_sources_tenant ON synced_sources(tenant_id, sync_status);
CREATE INDEX IF NOT EXISTS idx_synced_sources_next_sync ON synced_sources(next_sync_at) WHERE sync_status = 'success';

-- 3. Extender tabla tenants para preferencias de registro
ALTER TABLE tenants 
ADD COLUMN IF NOT EXISTS preferred_auth_provider VARCHAR(20),
ADD COLUMN IF NOT EXISTS allow_oauth_registration BOOLEAN DEFAULT TRUE;

-- 4. Extender tabla knowledge_chunks
-- fuente_tipo ya soporta 'excel' y 'csv' en la base de datos (según init-db.sql)
ALTER TABLE knowledge_chunks
ADD COLUMN IF NOT EXISTS synced_source_id UUID REFERENCES synced_sources(id) ON DELETE CASCADE;

-- 5. Crear índice compuesto para buscar eficientemente por agent y synced_source
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_synced_source 
ON knowledge_chunks(agent_id, synced_source_id) WHERE synced_source_id IS NOT NULL;

-- 6. Tabla de logs de sincronización
CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    synced_source_id UUID NOT NULL REFERENCES synced_sources(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE CASCADE,
    
    sync_started_at TIMESTAMPTZ DEFAULT NOW(),
    sync_completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    status VARCHAR(20) NOT NULL CHECK (status IN ('started', 'success', 'failed', 'partial')),
    error_message TEXT,
    
    rows_fetched INTEGER,
    rows_processed INTEGER,
    changes_detected JSONB,
    
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_sync_logs_source ON sync_logs(synced_source_id, sync_started_at DESC);
