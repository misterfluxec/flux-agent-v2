BEGIN;

-- ============================================
-- TABLA PRINCIPAL: knowledge_items
-- ============================================
CREATE TABLE IF NOT EXISTS knowledge_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    
    -- Metadatos básicos
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type VARCHAR(50) NOT NULL CHECK (type IN ('file', 'web', 'database', 'manual')),
    source_type VARCHAR(50) CHECK (source_type IN ('csv', 'xlsx', 'pdf', 'url', 'postgres', 'mysql')),
    
    -- Estado del proceso
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending', 'processing', 'indexed', 'error', 'disabled'
    )),
    progress INTEGER DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
    
    -- Archivos y rutas
    file_path TEXT,
    file_size BIGINT,
    file_hash VARCHAR(64), -- Para detectar cambios y evitar re-indexar
    
    -- Configuración de sincronización
    sync_enabled BOOLEAN DEFAULT false,
    sync_frequency VARCHAR(20) CHECK (sync_frequency IN ('hourly', 'daily', 'weekly', 'monthly')),
    sync_last_run TIMESTAMP,
    sync_next_run TIMESTAMP,
    webhook_url TEXT,
    
    -- Métricas de calidad
    vectors_count INTEGER DEFAULT 0,
    chunks_count INTEGER DEFAULT 0,
    avg_similarity_score FLOAT, -- Precisión promedio en búsquedas de prueba
    
    -- Mapeo de columnas (para archivos estructurados)
    column_mapping JSONB, -- {"name": "producto", "price": "precio", ...}
    
    -- Metadatos extensibles
    metadata JSONB DEFAULT '{}'::jsonb,
    
    -- Auditoría
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES usuarios(id),
    
    -- Soft delete
    is_active BOOLEAN DEFAULT true,
    deleted_at TIMESTAMP
);

-- ============================================
-- ÍNDICES ESTRATÉGICOS
-- ============================================

-- Búsqueda por tenant + estado (consulta más frecuente)
CREATE INDEX IF NOT EXISTS idx_knowledge_items_tenant_status 
ON knowledge_items(tenant_id, status) 
WHERE is_active = true;

-- Búsqueda por tipo de fuente
CREATE INDEX IF NOT EXISTS idx_knowledge_items_type 
ON knowledge_items(type, source_type) 
WHERE is_active = true;

-- Sincronizaciones pendientes
CREATE INDEX IF NOT EXISTS idx_knowledge_items_sync_due 
ON knowledge_items(sync_next_run) 
WHERE sync_enabled = true AND is_active = true;

-- Búsqueda por nombre (para UI)
CREATE INDEX IF NOT EXISTS idx_knowledge_items_name_search 
ON knowledge_items USING gin(to_tsvector('spanish', name));

-- ============================================
-- ROW LEVEL SECURITY (AISLAMIENTO MULTI-TENANT)
-- ============================================

ALTER TABLE knowledge_items ENABLE ROW LEVEL SECURITY;

-- Política: cada tenant solo ve sus propios items
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'knowledge_items' AND policyname = 'tenant_isolation_policy'
    ) THEN
        CREATE POLICY tenant_isolation_policy ON knowledge_items
            FOR ALL
            USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::uuid);
    END IF;
END
$$;

-- Política: admin_write_policy (Adaptado para nuestra DB si existe roles, pero como no hay tabla user_roles explícita, la simplificamos a los dueños)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'knowledge_items' AND policyname = 'admin_write_policy'
    ) THEN
        CREATE POLICY admin_write_policy ON knowledge_items
            FOR UPDATE
            USING (
                EXISTS (
                    SELECT 1 FROM usuarios u
                    WHERE u.id = current_setting('app.current_user_id', true)::uuid
                    AND u.tenant_id = knowledge_items.tenant_id
                )
            );
    END IF;
END
$$;

-- ============================================
-- TRIGGERS DE AUDITORÍA
-- ============================================

CREATE OR REPLACE FUNCTION update_knowledge_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger 
        WHERE tgname = 'trigger_knowledge_updated_at'
    ) THEN
        CREATE TRIGGER trigger_knowledge_updated_at
            BEFORE UPDATE ON knowledge_items
            FOR EACH ROW
            EXECUTE FUNCTION update_knowledge_updated_at();
    END IF;
END
$$;

-- ============================================
-- ALTERAR KNOWLEDGE_CHUNKS EXISTENTE
-- ============================================
-- Añadir llave foránea si no existe
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name='knowledge_chunks' AND column_name='knowledge_item_id'
    ) THEN
        ALTER TABLE knowledge_chunks ADD COLUMN knowledge_item_id UUID REFERENCES knowledge_items(id) ON DELETE CASCADE;
    END IF;
END
$$;

COMMIT;
