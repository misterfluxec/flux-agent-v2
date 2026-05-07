-- =============================================================================
-- MIGRACIÓN 011: UNIFICACIÓN DE TABLA AGENTS
-- =============================================================================
-- Agrega columnas faltantes para compatibilidad con frontend y backend
-- Une las estructuras de init-db.sql y migraciones existentes

-- Columnas para compatibilidad con frontend (wizard)
ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50) DEFAULT 'sales';
ALTER TABLE agents ADD COLUMN IF NOT EXISTS specialty VARCHAR(100);
ALTER TABLE agents ADD COLUMN IF NOT EXISTS system_prompt TEXT;

-- Columna para scripts de ventas (usada por backend)
ALTER TABLE agents ADD COLUMN IF NOT EXISTS script_ventas JSONB DEFAULT '{"fases": [], "reglas": [], "scripts": [], "escalacion": {"enabled": true, "keywords": []}}';

-- Crear índices para las nuevas columnas
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);
CREATE INDEX IF NOT EXISTS idx_agents_specialty ON agents(specialty);
CREATE INDEX IF NOT EXISTS idx_agents_script_ventas ON agents USING GIN(script_ventas);

-- Comentarios para las nuevas columnas
COMMENT ON COLUMN agents.agent_type IS 'Tipo de agente: sales, support, bookings, custom';
COMMENT ON COLUMN agents.specialty IS 'Especialidad del agente: zapatillas_deportivas, soporte_tecnico, etc.';
COMMENT ON COLUMN agents.system_prompt IS 'Prompt principal del sistema (instrucciones + personalidad)';
COMMENT ON COLUMN agents.script_ventas IS 'Scripts de ventas en formato JSON para agentes de ventas';

-- Actualizar valores por defecto para compatibilidad
UPDATE agents SET 
    agent_type = CASE 
        WHEN area = 'Ventas' THEN 'sales'
        WHEN area = 'Soporte' THEN 'support'
        WHEN area = 'Reservas' THEN 'bookings'
        ELSE 'custom'
    END,
    specialty = COALESCE(tipo_negocio, 'general'),
    system_prompt = COALESCE(instrucciones, personalidad, 'Eres un asistente profesional.')
WHERE agent_type IS NULL OR specialty IS NULL OR system_prompt IS NULL;

-- Asegurar que todos los agentes activos tengan el script_ventas por defecto
UPDATE agents SET script_ventas = '{"fases": [], "reglas": [], "scripts": [], "escalacion": {"enabled": true, "keywords": []}}'
WHERE script_ventas IS NULL AND estado = 'activo';
