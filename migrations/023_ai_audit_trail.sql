-- Migration 023: AI Response Audit Trail
-- Fase 4C: El registro auditable de TODO lo que el AI Copilot responde.

CREATE TABLE IF NOT EXISTS ai_response_audit_log (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id           UUID NOT NULL,
    correlation_id      VARCHAR(100), -- Opcional, si la respuesta está atada a un incidente
    
    -- Provenance & Explainability
    prompt_version      VARCHAR(50) NOT NULL,
    context_version     VARCHAR(10) NOT NULL,
    sources_used        JSONB NOT NULL,
    confidence          NUMERIC(5,4) NOT NULL,
    
    -- La respuesta exacta (inmutable)
    generated_response  TEXT NOT NULL,
    
    -- Metadatos del Modelo
    model_used          VARCHAR(100) NOT NULL,
    token_count         INTEGER,
    latency_ms          INTEGER,
    
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_ai_audit_log_tenant 
    ON ai_response_audit_log(tenant_id, created_at DESC);

CREATE INDEX idx_ai_audit_log_correlation 
    ON ai_response_audit_log(tenant_id, correlation_id);

-- Esta tabla DEBE ser estrictamente append-only (auditoría)
ALTER TABLE ai_response_audit_log ENABLE ROW LEVEL SECURITY;
CREATE POLICY ai_audit_log_rls ON ai_response_audit_log
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

-- Idealmente se crea un trigger para prevenir UPDATE o DELETE.
