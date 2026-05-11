-- Migration 021: Business Memory Layer Refinements
-- Desacopla la memoria histórica del event_outbox e introduce snapshots inmutables.

-- ─────────────────────────────────────────────
-- 1. Operational Event Store
-- ─────────────────────────────────────────────
-- Almacén histórico separado del event_outbox transaccional.
-- Optimizado para analítica, replay histórico y AI context.
CREATE TABLE IF NOT EXISTS operational_event_store (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID NOT NULL,
    domain          VARCHAR(50) NOT NULL, -- commerce, inventory, payments, connectors...
    event_type      VARCHAR(255) NOT NULL,
    correlation_id  VARCHAR(100),
    payload         JSONB NOT NULL,
    retention_tier  VARCHAR(20) DEFAULT 'WARM', -- HOT/WARM/COLD
    stored_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_op_event_store_tenant_domain 
    ON operational_event_store(tenant_id, domain, stored_at DESC);
CREATE INDEX idx_op_event_store_correlation 
    ON operational_event_store(tenant_id, correlation_id);

ALTER TABLE operational_event_store ENABLE ROW LEVEL SECURITY;
CREATE POLICY op_event_store_rls ON operational_event_store
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));


-- ─────────────────────────────────────────────
-- 2. Tenant Memory Snapshots (Time-Series)
-- ─────────────────────────────────────────────
-- Reemplaza a tenant_memory_profiles con un enfoque append-only
-- para permitir análisis de tendencias y degradación temporal.
DROP TABLE IF EXISTS tenant_memory_profiles;

CREATE TABLE IF NOT EXISTS tenant_memory_snapshots (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL,
    
    aggregation_window      VARCHAR(10) NOT NULL CHECK (aggregation_window IN ('5min', '1h', '24h', 'weekly')),
    window_start            TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end              TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Métricas estructuradas en JSON para máxima flexibilidad y evolución sin DDL
    metrics_json            JSONB NOT NULL DEFAULT '{}',
    
    -- Composite Score derivado de la agregación
    operational_stability   NUMERIC(5,2), 
    risk_level              VARCHAR(10) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    
    computed_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE (tenant_id, aggregation_window, window_start)
);

CREATE INDEX idx_tenant_memory_snapshots_time
    ON tenant_memory_snapshots(tenant_id, aggregation_window, window_start DESC);

ALTER TABLE tenant_memory_snapshots ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_memory_snapshots_rls ON tenant_memory_snapshots
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));


-- ─────────────────────────────────────────────
-- 3. Customer Memory Profiles (Expansión)
-- ─────────────────────────────────────────────
-- Se añaden nuevos scores para predecir soporte, priorización y fricción operativa.

ALTER TABLE customer_memory_profiles 
    ADD COLUMN IF NOT EXISTS operational_risk_level VARCHAR(10) CHECK (operational_risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    ADD COLUMN IF NOT EXISTS support_load_score NUMERIC(5,4) DEFAULT 0.0, -- Propensión a generar tickets
    ADD COLUMN IF NOT EXISTS payment_recovery_rate NUMERIC(5,4) DEFAULT 1.0, -- % de éxito en reintentos
    ADD COLUMN IF NOT EXISTS fulfillment_reliability NUMERIC(5,4) DEFAULT 1.0, -- 1.0 = entregas perfectas
    ADD COLUMN IF NOT EXISTS last_incident_at TIMESTAMP WITH TIME ZONE;
