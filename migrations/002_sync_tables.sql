BEGIN;

CREATE TABLE IF NOT EXISTS connected_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    provider_user_id VARCHAR(255) NOT NULL,
    provider_email VARCHAR(255),
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT,
    token_expires_at TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, provider, provider_user_id)
);

CREATE TABLE IF NOT EXISTS synced_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    account_id UUID REFERENCES connected_accounts(id) ON DELETE CASCADE,
    source_id VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    sync_status VARCHAR(50) DEFAULT 'pending',
    sync_error_message TEXT,
    last_synced_at TIMESTAMPTZ,
    next_sync_at TIMESTAMPTZ,
    rows_processed INTEGER DEFAULT 0,
    creado_en TIMESTAMPTZ DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    synced_source_id VARCHAR(255) NOT NULL, -- Keep as string because local files use local_filename
    status VARCHAR(50) NOT NULL,
    rows_processed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_started_at TIMESTAMPTZ DEFAULT NOW(),
    sync_completed_at TIMESTAMPTZ
);

COMMIT;
