-- =============================================================================
-- MIGRATION 007: WHATSAPP USAGE TRACKING
-- =============================================================================
-- Tabla para tracking de conversaciones y costos de WhatsApp
-- =============================================================================

CREATE TABLE IF NOT EXISTS whatsapp_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    -- Identificación
    phone_number_id VARCHAR(100),
    conversation_id VARCHAR(100),
    recipient_phone VARCHAR(50) NOT NULL,
    
    -- Clasificación
    conversation_type VARCHAR(20) NOT NULL CHECK (
        conversation_type IN ('service', 'utility', 'authentication', 'marketing')
    ),
    channel_used VARCHAR(20) NOT NULL CHECK (
        channel_used IN ('evolution', 'cloud_api')
    ),
    
    -- Costos (USD)
    meta_cost_usd DECIMAL(10, 6) DEFAULT 0,
    fluxagent_markup DECIMAL(10, 6) DEFAULT 0,
    total_cost_usd DECIMAL(10, 6) GENERATED ALWAYS AS (meta_cost_usd + fluxagent_markup) STORED,
    
    -- Metadata
    message_count INTEGER DEFAULT 1,
    first_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Auditoría
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices para reporting
CREATE INDEX idx_whatsapp_usage_tenant_month 
ON whatsapp_usage(tenant_id, first_message_at);

CREATE INDEX idx_whatsapp_usage_phone 
ON whatsapp_usage(recipient_phone, first_message_at);

CREATE INDEX idx_whatsapp_usage_conversation 
ON whatsapp_usage(conversation_id);

-- Tabla de métricas de salud del número
CREATE TABLE IF NOT EXISTS whatsapp_health (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Métricas
    quality_rating VARCHAR(20) DEFAULT 'UNKNOWN' CHECK (
        quality_rating IN ('GREEN', 'YELLOW', 'RED', 'UNKNOWN')
    ),
    conversations_today INTEGER DEFAULT 0,
    conversations_limit INTEGER DEFAULT 1000,
    delivery_rate DECIMAL(5, 2) DEFAULT 100.00,
    error_count_today INTEGER DEFAULT 0,
    blocks_last_24h INTEGER DEFAULT 0,
    
    -- Última actualización
    last_checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    UNIQUE(tenant_id)
);

-- Función para actualizar métricas diarias
CREATE OR REPLACE FUNCTION update_whatsapp_health_metrics()
RETURNS VOID AS $$
BEGIN
    INSERT INTO whatsapp_health (tenant_id, conversations_today, delivery_rate, last_checked_at)
    SELECT 
        tenant_id,
        COUNT(*) as conversations_today,
        COALESCE(
            (SUM(CASE WHEN channel_used = 'cloud_api' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0)),
            100.0
        ) as delivery_rate,
        NOW()
    FROM whatsapp_usage
    WHERE first_message_at >= CURRENT_DATE
    ON CONFLICT (tenant_id) DO UPDATE SET
        conversations_today = EXCLUDED.conversations_today,
        delivery_rate = EXCLUDED.delivery_rate,
        last_checked_at = EXCLUDED.last_checked_at,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar métricas cada hora
CREATE OR REPLACE FUNCTION trigger_update_whatsapp_health()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.first_message_at >= CURRENT_DATE THEN
        INSERT INTO whatsapp_health (tenant_id, conversations_today, last_checked_at)
        VALUES (NEW.tenant_id, 1, NOW())
        ON CONFLICT (tenant_id) DO UPDATE SET
            conversations_today = whatsapp_health.conversations_today + 1,
            last_checked_at = NOW(),
            updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER whatsapp_usage_health_trigger
AFTER INSERT ON whatsapp_usage
FOR EACH ROW
EXECUTE FUNCTION trigger_update_whatsapp_health();

COMMENT ON TABLE whatsapp_usage IS 'Tracking de conversaciones y costos de WhatsApp por tenant';
COMMENT ON TABLE whatsapp_health IS 'Métricas de salud del número de WhatsApp';