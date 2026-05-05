BEGIN;

CREATE OR REPLACE FUNCTION hybrid_search(
    query_text TEXT,
    query_embedding VECTOR(768), -- Asumiendo nomic-embed-text (dimension 768)
    match_count INT,
    p_tenant_id UUID
) RETURNS TABLE (
    id UUID,
    content TEXT,
    fuente_nombre VARCHAR,
    similarity FLOAT
) LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT 
        kc.id,
        kc.contenido as content,
        kc.fuente_nombre,
        (1 - (kc.embedding <=> query_embedding)) AS similarity
    FROM knowledge_chunks kc
    WHERE kc.tenant_id = p_tenant_id
    ORDER BY kc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

COMMIT;
