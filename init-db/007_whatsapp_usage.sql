-- migration_007_whatsapp_usage.sql
CREATE TABLE whatsapp_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    
    -- Identificación
    phone_number_id VARCHAR(100),
    recipient_phone VARCHAR(20),
    conversation_id VARCHAR(100),  -- ID único de ventana 24h
    
    -- Clasificación
    conversation_type VARCHAR(20) CHECK (conversation_type IN (
        'service', 'utility', 'authentication', 'marketing'
    )),
    channel_used VARCHAR(20) CHECK (channel_used IN ('evolution', 'cloud_api')),
    
    -- Costos (en USD)
    meta_cost_usd DECIMAL(10, 6) DEFAULT 0,
    fluxagent_markup_usd DECIMAL(10, 6) DEFAULT 0,
    
    -- Metadata
    message_count INTEGER DEFAULT 1,
    first_message_at TIMESTAMP DEFAULT NOW(),
    last_message_at TIMESTAMP DEFAULT NOW(),
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Índices para reporting
CREATE INDEX idx_whatsapp_usage_tenant_date 
ON whatsapp_usage(tenant_id, first_message_at);

CREATE INDEX idx_whatsapp_usage_conversation 
ON whatsapp_usage(conversation_id);

-- Vista para resumen mensual (opcional)
CREATE OR REPLACE VIEW v_monthly_whatsapp_costs AS
SELECT 
    tenant_id,
    date_trunc('month', first_message_at) AS billing_month,
    SUM(meta_cost_usd) AS total_meta_costs,
    SUM(fluxagent_markup_usd) AS total_markup,
    COUNT(DISTINCT conversation_id) AS total_conversations
FROM whatsapp_usage
GROUP BY tenant_id, date_trunc('month', first_message_at);
