-- Migration 022: Memory Schema Versioning
-- Fase 4C: OBLIGATORIO antes de exponer contexto al LLM.

-- 1. Versioning para Tenant Memory Snapshots
ALTER TABLE tenant_memory_snapshots
ADD COLUMN IF NOT EXISTS memory_schema_version VARCHAR(10) DEFAULT 'v1';

-- 2. Versioning para Customer Memory Profiles
ALTER TABLE customer_memory_profiles
ADD COLUMN IF NOT EXISTS memory_schema_version VARCHAR(10) DEFAULT 'v1';

-- Actualizar registros existentes por si acaso
UPDATE tenant_memory_snapshots SET memory_schema_version = 'v1' WHERE memory_schema_version IS NULL;
UPDATE customer_memory_profiles SET memory_schema_version = 'v1' WHERE memory_schema_version IS NULL;
