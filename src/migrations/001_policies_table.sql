-- Migración 001: Tabla flux_policies
-- Idempotente: segura de ejecutar múltiples veces

CREATE TABLE IF NOT EXISTS flux_policies (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id     UUID,
    name          VARCHAR(120) NOT NULL,
    description   TEXT         NOT NULL DEFAULT '',
    conditions    JSONB        NOT NULL DEFAULT '[]',
    action        VARCHAR(30)  NOT NULL
                  CHECK (action IN (
                    'allow','deny','require_approval',
                    'modify','log_only'
                  )),
    priority      INTEGER      NOT NULL DEFAULT 0,
    enabled       BOOLEAN      NOT NULL DEFAULT TRUE,
    tenant_plans  JSONB        NOT NULL DEFAULT '[]',
    industries    JSONB        NOT NULL DEFAULT '[]',
    tools         JSONB,
    modifications JSONB        NOT NULL DEFAULT '{}',
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_policies_tenant
    ON flux_policies (tenant_id)
    WHERE enabled = TRUE;

CREATE INDEX IF NOT EXISTS idx_policies_tools
    ON flux_policies USING GIN (tools)
    WHERE enabled = TRUE AND tools IS NOT NULL;

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_policies_updated_at
    ON flux_policies;
CREATE TRIGGER trg_policies_updated_at
    BEFORE UPDATE ON flux_policies
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TABLE IF NOT EXISTS flux_policy_audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id       UUID,
    tool_name       VARCHAR(120),
    final_decision  VARCHAR(30),
    evaluations     JSONB NOT NULL DEFAULT '[]',
    context_snapshot JSONB,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_policy_audit_tenant
    ON flux_policy_audit_log (tenant_id, created_at DESC);