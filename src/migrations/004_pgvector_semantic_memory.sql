-- Migración 004: Memoria semántica con pgvector
-- Requiere PostgreSQL 14+ con extensión pgvector

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS flux_semantic_memory (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID,
    customer_id VARCHAR(120) NOT NULL,
    agent_id    VARCHAR(120),
    content     TEXT         NOT NULL,
    role        VARCHAR(20)  NOT NULL DEFAULT 'user',
    embedding   vector(768),
    metadata    JSONB        NOT NULL DEFAULT '{}',
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- HNSW: búsqueda aproximada de alta velocidad (mejor para RAG)
CREATE INDEX IF NOT EXISTS idx_semantic_memory_hnsw
    ON flux_semantic_memory
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_semantic_memory_customer
    ON flux_semantic_memory (customer_id, created_at DESC);
