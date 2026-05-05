CREATE TABLE IF NOT EXISTS canales_config (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,

    canal VARCHAR(50) NOT NULL CHECK (canal IN ('whatsapp', 'telegram', 'instagram', 'web_chat')),
    instancia_nombre VARCHAR(255) NOT NULL,
    
    -- Credenciales / Tokens (depende del canal)
    token_acceso TEXT,
    webhook_url TEXT,

    estado VARCHAR(50) DEFAULT 'activo' CHECK (estado IN ('activo', 'inactivo', 'desconectado')),
    
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Una instancia con un nombre particular es única por tenant
    UNIQUE(tenant_id, canal, instancia_nombre)
);

ALTER TABLE canales_config ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_canales_tenant ON canales_config(tenant_id);

CREATE POLICY tenant_isolation_canales ON canales_config
    USING (tenant_id = current_setting('app.current_tenant_id', TRUE)::UUID);

CREATE TRIGGER trg_canales_actualizado
    BEFORE UPDATE ON canales_config
    FOR EACH ROW EXECUTE FUNCTION fn_actualizar_timestamp();
