-- =============================================================================
-- MIGRACIÓN 012: ESTANDARIZACIÓN DE COLUMNAS (INGLÉS)
-- =============================================================================
-- Opcional pero recomendado para consistencia total
-- Convierte columnas de español a inglés en tabla agents
-- =============================================================================

-- NOTA: Esta migración es opcional y puede ser peligrosa si ya hay datos
-- Considerar hacer backup antes de ejecutar

-- Renombrar columnas principales a inglés
DO $$
BEGIN
    -- Verificar si las columnas existen antes de renombrar
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'nombre') THEN
        ALTER TABLE agents RENAME COLUMN nombre TO name;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'estado') THEN
        ALTER TABLE agents RENAME COLUMN estado TO status;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'creado_en') THEN
        ALTER TABLE agents RENAME COLUMN creado_en TO created_at;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'actualizado_en') THEN
        ALTER TABLE agents RENAME COLUMN actualizado_en TO updated_at;
    END IF;
    
    -- Otras columnas opcionales
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'descripcion') THEN
        ALTER TABLE agents RENAME COLUMN descripcion TO description;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'genero') THEN
        ALTER TABLE agents RENAME COLUMN genero TO gender;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'humor') THEN
        ALTER TABLE agents RENAME COLUMN humor TO tone;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'personalidad') THEN
        ALTER TABLE agents RENAME COLUMN personalidad TO personality;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'idioma') THEN
        ALTER TABLE agents RENAME COLUMN idioma TO language;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'tono') THEN
        ALTER TABLE agents RENAME COLUMN tono TO tone_of_voice;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'coleccion_rag') THEN
        ALTER TABLE agents RENAME COLUMN coleccion_rag TO rag_collection;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'tipo_negocio') THEN
        ALTER TABLE agents RENAME COLUMN tipo_negocio TO business_type;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'objetivo') THEN
        ALTER TABLE agents RENAME COLUMN objetivo TO objective;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'instrucciones') THEN
        ALTER TABLE agents RENAME COLUMN instrucciones TO instructions;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'modelo') THEN
        ALTER TABLE agents RENAME COLUMN modelo TO model;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'temperatura') THEN
        ALTER TABLE agents RENAME COLUMN temperatura TO temperature;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'max_tokens') THEN
        ALTER TABLE agents RENAME COLUMN max_tokens TO max_tokens;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'canales') THEN
        ALTER TABLE agents RENAME COLUMN canales TO channels;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'horario_inicio') THEN
        ALTER TABLE agents RENAME COLUMN horario_inicio TO schedule_start;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'horario_fin') THEN
        ALTER TABLE agents RENAME COLUMN horario_fin TO schedule_end;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'dias_atencion') THEN
        ALTER TABLE agents RENAME COLUMN dias_atencion TO attention_days;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'mensaje_fuera_horario') THEN
        ALTER TABLE agents RENAME COLUMN mensaje_fuera_horario TO off_hours_message;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'script_ventas') THEN
        ALTER TABLE agents RENAME COLUMN script_ventas TO sales_script;
    END IF;
    
    IF EXISTS (SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'agents' AND column_name = 'area') THEN
        ALTER TABLE agents RENAME COLUMN area TO area;
    END IF;
END $$;

-- Actualizar índices si es necesario
DROP INDEX IF EXISTS idx_agents_tenant_status;
CREATE INDEX IF NOT EXISTS idx_agents_tenant_status ON agents(tenant_id, status);

DROP INDEX IF EXISTS idx_agents_type;
CREATE INDEX IF NOT EXISTS idx_agents_type ON agents(agent_type);

DROP INDEX IF EXISTS idx_agents_specialty;
CREATE INDEX IF NOT EXISTS idx_agents_specialty ON agents(specialty);

DROP INDEX IF EXISTS idx_agents_script_ventas;
CREATE INDEX IF NOT EXISTS idx_agents_sales_script ON agents USING GIN(sales_script);

-- Actualizar comentarios
COMMENT ON TABLE agents IS 'Agents AI table with standardized English column names';
COMMENT ON COLUMN agents.id IS 'Primary key UUID';
COMMENT ON COLUMN agents.tenant_id IS 'Foreign key to tenants table';
COMMENT ON COLUMN agents.name IS 'Agent display name';
COMMENT ON COLUMN agents.status IS 'Agent status: draft, testing, active, paused';
COMMENT ON COLUMN agents.agent_type IS 'Agent type: sales, support, bookings, custom';
COMMENT ON COLUMN agents.specialty IS 'Agent specialty area';
COMMENT ON COLUMN agents.system_prompt IS 'System prompt for LLM';
COMMENT ON COLUMN agents.sales_script IS 'Sales scripts in JSON format';

-- Log de migración
INSERT INTO migration_log (migration_name, executed_at, description) 
VALUES ('012_standardize_agents', NOW(), 'Standardized agents table column names to English')
ON CONFLICT (migration_name) DO NOTHING;

-- NOTA: Después de esta migración, se debe actualizar:
-- 1. Mappers en src/core/db/mappers.py
-- 2. Schemas Pydantic en domain/agents/schemas.py
-- 3. Queries SQL en todos los routers
-- 4. Documentación y código frontend
