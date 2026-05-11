-- =============================================================================
-- MIGRATION 010: EVENT LOG & UNIFIED TIMELINE (SPRINT 4.1)
-- =============================================================================
-- Esta tabla implementa el patrón Event Sourcing (append-only).
-- Es la fuente inmutable de la verdad para todas las operaciones de negocio.
-- =============================================================================

CREATE TABLE IF NOT EXISTS event_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificación del evento
    event_type VARCHAR(100) NOT NULL,  -- e.g., "quote.generated", "payment.completed"
    event_id VARCHAR(255) NOT NULL,    -- ID único del evento original
    aggregate_type VARCHAR(50) NOT NULL,        -- e.g., "lead", "quote", "order"
    aggregate_id UUID NOT NULL,                 -- ID de la entidad principal
    
    -- Contexto multi-tenant
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Payload completo (JSONB para flexibilidad)
    payload JSONB NOT NULL,
    
    -- Event Versioning: permite evolucionar payloads sin romper compatibilidad histórica
    event_version SMALLINT NOT NULL DEFAULT 1,
    
    -- Inteligencia operacional (calculada por SeverityEngine, no manual)
    severity VARCHAR(20) DEFAULT 'low',         -- "low", "medium", "high", "critical"
    business_impact VARCHAR(50),                -- "revenue", "ops", "retention", "security"
    
    -- Metadatos de sistema y distributed tracing
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    correlation_id UUID,               -- Flujo completo (ej: lead → quote → payment)
    causation_id UUID,                 -- Evento específico que causó este
    
    -- Constraints
    UNIQUE(tenant_id, event_id)
);

-- Índices optimizados para las consultas de la timeline y analytics
CREATE INDEX IF NOT EXISTS idx_event_log_tenant_agg ON event_log (tenant_id, aggregate_type, aggregate_id);
CREATE INDEX IF NOT EXISTS idx_event_log_type_time ON event_log (event_type, occurred_at);
CREATE INDEX IF NOT EXISTS idx_event_log_correlation ON event_log (correlation_id) WHERE correlation_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_event_log_severity ON event_log (severity) WHERE severity IN ('high', 'critical');

-- Política RLS para aislamiento
ALTER TABLE event_log ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'event_log' AND policyname = 'tenant_isolation_event_log'
    ) THEN
        CREATE POLICY tenant_isolation_event_log ON event_log 
            USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);
        RAISE NOTICE '✅ Policy RLS agregada a event_log';
    END IF;
END $$;
