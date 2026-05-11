-- =============================================================================
-- MIGRATION 009: COMMERCIAL PLAYBOOKS (SPRINT 4.1)
-- =============================================================================
-- Esta tabla almacena la configuración de estrategia comercial y personalidad
-- de los agentes por industria, desacoplando la identidad de la lógica de ventas.
-- =============================================================================

CREATE TABLE IF NOT EXISTS commercial_playbooks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Identificación
    industry VARCHAR(50) NOT NULL,  -- e.g. "retail", "clinic", "services"
    version VARCHAR(20) DEFAULT '1.0',
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Configuración operacional (SEPARADOS para mejor control y edición UI)
    personality JSONB DEFAULT '{}'::jsonb,           -- { "tone": "consultivo", "verbosity": "medium", "urgency_style": "soft" }
    commercial_strategy JSONB DEFAULT '{}'::jsonb,     -- { "upsell_style": "suggestive", "discount_policy": "approval_required", "objection_rules": {...} }
    
    workflows JSONB DEFAULT '[]'::jsonb,             -- ["quote_followup_48h", "low_stock_alert"]
    sla_rules JSONB DEFAULT '{}'::jsonb,             -- { "first_response_sec": 30, "quote_valid_hours": 48 }
    kpi_targets JSONB DEFAULT '{}'::jsonb,           -- { "conversion_pct": 15, "aov_increase_pct": 10 }
    
    -- Metadata extensible
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Config Hash: SHA-256 del config actual. Permite detectar drift, invalidar cache y rollback.
    config_hash VARCHAR(16),
    
    is_active BOOLEAN DEFAULT true,
    is_system_template BOOLEAN DEFAULT false,        -- Templates globales vs custom del tenant
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(tenant_id, industry, version)
);

-- Relación agente → playbook (referencia, no copia)
-- Usamos DO block para evitar error si la columna ya existe
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='agentes' AND column_name='playbook_id') THEN
        ALTER TABLE agentes ADD COLUMN playbook_id UUID REFERENCES commercial_playbooks(id) ON DELETE SET NULL;
        RAISE NOTICE '✅ Columna playbook_id agregada a agentes';
    END IF;
END $$;

-- Índices para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_playbooks_tenant_industry ON commercial_playbooks(tenant_id, industry);
CREATE INDEX IF NOT EXISTS idx_playbooks_system ON commercial_playbooks(is_system_template) WHERE is_system_template = true;
CREATE INDEX IF NOT EXISTS idx_agents_playbook ON agentes(playbook_id) WHERE playbook_id IS NOT NULL;

-- Habilitar RLS
ALTER TABLE commercial_playbooks ENABLE ROW LEVEL SECURITY;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies WHERE tablename = 'commercial_playbooks' AND policyname = 'tenant_isolation_playbooks'
    ) THEN
        CREATE POLICY tenant_isolation_playbooks ON commercial_playbooks 
            USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID OR is_system_template = true);
        RAISE NOTICE '✅ Policy RLS agregada a commercial_playbooks';
    END IF;
END $$;
