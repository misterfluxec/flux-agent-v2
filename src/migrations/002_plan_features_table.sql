-- Migración 002: Tabla unificada de planes
-- Reemplaza PLAN_LIMITS hardcodeado en 3 archivos

CREATE TABLE IF NOT EXISTS flux_plan_features (
    id                      UUID PRIMARY KEY
                            DEFAULT gen_random_uuid(),
    plan_key                VARCHAR(30) UNIQUE NOT NULL,
    display_name            VARCHAR(60) NOT NULL,
    price_usd               NUMERIC(10,2) NOT NULL DEFAULT 0,
    sort_order              INTEGER NOT NULL DEFAULT 0,

    -- Límites de negocio (de plan_limits.py)
    max_agents              INTEGER NOT NULL DEFAULT 1,
    max_active_quotes       INTEGER NOT NULL DEFAULT 5,
    monthly_interactions    INTEGER NOT NULL DEFAULT 100,
    allowed_workflows       JSONB NOT NULL DEFAULT '[]',

    -- Límites de mensajería (de billing_router.py)
    max_messages_month      INTEGER NOT NULL DEFAULT 100,

    -- Rate limiting (de rate_limit/rules.py)
    requests_per_hour       INTEGER NOT NULL DEFAULT 100,
    messages_per_minute     INTEGER NOT NULL DEFAULT 10,
    ai_requests_per_minute  INTEGER NOT NULL DEFAULT 5,
    file_uploads_per_hour   INTEGER NOT NULL DEFAULT 5,

    is_active   BOOLEAN     NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

DROP TRIGGER IF EXISTS trg_plan_features_updated_at
    ON flux_plan_features;
CREATE TRIGGER trg_plan_features_updated_at
    BEFORE UPDATE ON flux_plan_features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Seed: planes unificados con datos reales
INSERT INTO flux_plan_features (
    plan_key, display_name, price_usd, sort_order,
    max_agents, max_active_quotes, monthly_interactions,
    allowed_workflows, max_messages_month,
    requests_per_hour, messages_per_minute,
    ai_requests_per_minute, file_uploads_per_hour
) VALUES
(
    'free', 'Free', 0, 0,
    1, 5, 100,
    '["cart_recovery"]', 100,
    100, 10, 5, 5
),
(
    'starter', 'Starter', 29, 1,
    1, 5, 100,
    '["cart_recovery"]', 2000,
    500, 50, 25, 20
),
(
    'pro', 'Pro', 99, 2,
    3, 50, 1000,
    '["cart_recovery","appointment_reminder_24h","quote_followup_48h"]',
    10000,
    2000, 200, 100, 100
),
(
    'enterprise', 'Enterprise', 299, 3,
    -1, -1, -1,
    'null', 100000,
    10000, 1000, 500, 500
)
ON CONFLICT (plan_key) DO UPDATE SET
    price_usd              = EXCLUDED.price_usd,
    max_agents             = EXCLUDED.max_agents,
    max_active_quotes      = EXCLUDED.max_active_quotes,
    monthly_interactions   = EXCLUDED.monthly_interactions,
    allowed_workflows      = EXCLUDED.allowed_workflows,
    max_messages_month     = EXCLUDED.max_messages_month,
    requests_per_hour      = EXCLUDED.requests_per_hour,
    messages_per_minute    = EXCLUDED.messages_per_minute,
    ai_requests_per_minute = EXCLUDED.ai_requests_per_minute,
    file_uploads_per_hour  = EXCLUDED.file_uploads_per_hour,
    updated_at             = NOW();
