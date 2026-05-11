-- Migration 020: Business Memory Layer
-- Fase 4B: Converts raw operational events into structured semantic memory.
-- Both tables use JSONB for maximum flexibility as signals evolve.

-- ─────────────────────────────────────────────
-- Tenant Memory Profiles
-- Behavioral snapshots of the tenant's operational health over time.
-- Computed by background workers, NOT on-demand.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS tenant_memory_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id               UUID NOT NULL,
    
    -- Aggregation window metadata
    window_type             VARCHAR(10) NOT NULL CHECK (window_type IN ('5min', '1h', '24h', 'weekly')),
    window_start            TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end              TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Payment behavior signals
    payment_success_rate    NUMERIC(5,2),
    payment_failure_rate    NUMERIC(5,2),
    avg_payment_amount      NUMERIC(12,2),
    chargeback_count        INTEGER DEFAULT 0,
    
    -- Retry & DLQ pressure
    total_retries           INTEGER DEFAULT 0,
    dlq_events              INTEGER DEFAULT 0,
    retry_recovery_rate     NUMERIC(5,2),   -- % de retries que se recuperaron
    
    -- Inventory signals
    drift_events            INTEGER DEFAULT 0,
    reservation_pressure    NUMERIC(5,2),   -- reserved / total stock ratio
    fulfillment_velocity    NUMERIC(8,2),   -- units committed / day
    
    -- Connector signals
    sync_success_rate       NUMERIC(5,2),
    connector_failures      INTEGER DEFAULT 0,
    schema_changes          INTEGER DEFAULT 0,
    
    -- Composite operational score for this window
    operational_stability   NUMERIC(5,2),   -- 0-100 Business Stability Score
    risk_level              VARCHAR(10) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    
    -- Raw signals JSONB for flexibility
    raw_signals             JSONB DEFAULT '{}',
    
    computed_at             TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE (tenant_id, window_type, window_start)
);

CREATE INDEX idx_tenant_memory_tenant_window 
    ON tenant_memory_profiles (tenant_id, window_type, window_start DESC);

-- RLS: Tenant isolation
ALTER TABLE tenant_memory_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_memory_rls ON tenant_memory_profiles
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

-- ─────────────────────────────────────────────
-- Customer Memory Profiles
-- Per-customer behavioral scoring for risk detection and future AI context.
-- ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS customer_memory_profiles (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id                 UUID NOT NULL,
    tenant_id                   UUID NOT NULL,
    
    -- Risk scores (0.0 to 1.0)
    churn_risk_score            NUMERIC(5,4) DEFAULT 0.0,
    payment_reliability_score   NUMERIC(5,4) DEFAULT 1.0,  -- 1.0 = fully reliable
    refund_probability          NUMERIC(5,4) DEFAULT 0.0,
    
    -- Behavioral aggregates
    total_orders                INTEGER DEFAULT 0,
    total_ltv                   NUMERIC(12,2) DEFAULT 0.00,
    failed_payments_30d         INTEGER DEFAULT 0,
    avg_order_value             NUMERIC(12,2) DEFAULT 0.00,
    avg_days_between_orders     NUMERIC(6,2),
    
    -- Operational health
    operational_health_score    NUMERIC(5,2) DEFAULT 100.0, -- 0-100
    risk_level                  VARCHAR(10) CHECK (risk_level IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    
    -- Retry / friction signals
    total_retries_caused        INTEGER DEFAULT 0,
    webhook_failures_caused     INTEGER DEFAULT 0,
    
    -- Timestamps
    last_order_at               TIMESTAMP WITH TIME ZONE,
    last_payment_at             TIMESTAMP WITH TIME ZONE,
    last_computed_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE (customer_id, tenant_id)
);

CREATE INDEX idx_customer_memory_tenant 
    ON customer_memory_profiles (tenant_id, churn_risk_score DESC);

-- RLS
ALTER TABLE customer_memory_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY customer_memory_rls ON customer_memory_profiles
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));
