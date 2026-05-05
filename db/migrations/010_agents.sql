CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Identificación
    name VARCHAR(100) NOT NULL,
    avatar_url TEXT,
    
    -- Especialidad y tipo (clave para enrutamiento)
    agent_type VARCHAR(50) NOT NULL, -- 'sales', 'support', 'bookings', 'custom'
    specialty VARCHAR(100),          -- 'zapatillas_deportivas', 'soporte_tecnico', 'reservas_hoteleras'
    
    -- Configuración del agente
    system_prompt TEXT NOT NULL,
    tone VARCHAR(30) DEFAULT 'profesional',
    temperature FLOAT DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 500,
    
    -- Estado
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'testing', 'active', 'paused')),
    
    -- Auditoría
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Único por tenant + nombre
    UNIQUE(tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_agents_tenant_status ON agents(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
