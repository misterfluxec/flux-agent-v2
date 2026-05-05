ALTER TABLE agents ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50) DEFAULT 'sales';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS specialty VARCHAR(100);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS system_prompt TEXT DEFAULT 'Eres un asistente virtual.';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS tone VARCHAR(30) DEFAULT 'profesional';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS temperature FLOAT DEFAULT 0.7;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS max_tokens INTEGER DEFAULT 500;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'draft';

-- Update existing rows to have sensible defaults for the new non-null equivalent fields if needed.
-- But the ADD COLUMN IF NOT EXISTS is safe.

CREATE INDEX IF NOT EXISTS idx_agents_tenant_status ON agents(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
