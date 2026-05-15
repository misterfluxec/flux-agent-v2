-- Migración 003: Tablas del Workflow Runtime Engine

CREATE TABLE IF NOT EXISTS flux_workflow_definitions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID,
    name          VARCHAR(120) NOT NULL,
    version       INTEGER NOT NULL DEFAULT 1,
    definition    JSONB NOT NULL,
    is_active     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, name, version)
);

CREATE TABLE IF NOT EXISTS flux_workflow_runs (
    id                     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id              UUID NOT NULL,
    workflow_definition_id UUID NOT NULL REFERENCES
                           flux_workflow_definitions(id),
    status                 VARCHAR(20) NOT NULL DEFAULT 'running'
                           CHECK (status IN (
                             'running','suspended',
                             'completed','failed','cancelled'
                           )),
    current_node_id        VARCHAR(120),
    context                JSONB NOT NULL DEFAULT '{}',
    error_message          TEXT,
    started_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at           TIMESTAMPTZ,
    created_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at             TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_workflow_runs_tenant_status
    ON flux_workflow_runs (tenant_id, status)
    WHERE status IN ('running', 'suspended');

CREATE TABLE IF NOT EXISTS flux_workflow_step_runs (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id         UUID NOT NULL REFERENCES flux_workflow_runs(id)
                   ON DELETE CASCADE,
    node_id        VARCHAR(120) NOT NULL,
    node_type      VARCHAR(50) NOT NULL,
    status         VARCHAR(20) NOT NULL DEFAULT 'running'
                   CHECK (status IN (
                     'pending','running','suspended',
                     'completed','failed'
                   )),
    input_snapshot JSONB,
    output         JSONB,
    error_message  TEXT,
    started_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at   TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_step_runs_run_id
    ON flux_workflow_step_runs (run_id);

DROP TRIGGER IF EXISTS trg_workflow_runs_updated_at
    ON flux_workflow_runs;
CREATE TRIGGER trg_workflow_runs_updated_at
    BEFORE UPDATE ON flux_workflow_runs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
