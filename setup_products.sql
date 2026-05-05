CREATE TABLE IF NOT EXISTS productos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    codigo VARCHAR(100),
    nombre VARCHAR(255) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(10,2) DEFAULT 0.00,
    stock INTEGER DEFAULT 0,
    estado VARCHAR(50) DEFAULT 'activo',
    creado_en TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
ALTER TABLE productos ENABLE ROW LEVEL SECURITY;
CREATE INDEX IF NOT EXISTS idx_productos_tenant ON productos(tenant_id);
