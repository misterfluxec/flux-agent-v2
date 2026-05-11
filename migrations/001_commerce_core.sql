-- ==========================================
-- FLUXAGENT V2 — PHASE 0: COMMERCE CORE DB
-- Ejecutar en: PostgreSQL 14+
-- Tablas: catalog_items, offers, offer_items, resources, booking_slots, quotes, quote_items, orders, order_items
-- ==========================================

BEGIN;

-- 1. CATÁLOGO OPERACIONAL UNIVERSAL
CREATE TABLE IF NOT EXISTS catalog_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('physical_product', 'digital_product', 'service', 'subscription', 'booking', 'appointment', 'custom_offer')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    duration_minutes INTEGER,
    stock_quantity INTEGER DEFAULT 0,
    low_stock_threshold INTEGER DEFAULT 5,
    requires_booking BOOLEAN DEFAULT false,
    requires_payment BOOLEAN DEFAULT true,
    requires_human_approval BOOLEAN DEFAULT false,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_tenant_name UNIQUE (tenant_id, name)
);

-- 2. OFERTAS / PACKAGES
CREATE TABLE IF NOT EXISTS offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    catalog_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    base_price DECIMAL(10,2),
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    is_composite BOOLEAN DEFAULT false,
    min_quantity INTEGER DEFAULT 1,
    max_quantity INTEGER DEFAULT 999,
    valid_from TIMESTAMPTZ,
    valid_until TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS offer_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    offer_id UUID REFERENCES offers(id) ON DELETE CASCADE,
    catalog_item_id UUID NOT NULL REFERENCES catalog_items(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    role VARCHAR(50) DEFAULT 'main',
    UNIQUE(offer_id, catalog_item_id, role)
);

-- 3. RECURSOS OPERACIONALES
CREATE TABLE IF NOT EXISTS resources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('human', 'room', 'vehicle', 'equipment', 'virtual')),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    capacity INTEGER DEFAULT 1,
    timezone VARCHAR(50) DEFAULT 'UTC',
    user_id UUID REFERENCES usuarios(id) ON DELETE SET NULL,
    skills JSONB DEFAULT '[]'::jsonb,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(tenant_id, name)
);

-- 4. SLOTS DE RESERVA / APPOINTMENTS
CREATE TABLE IF NOT EXISTS booking_slots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    resource_id UUID REFERENCES resources(id) ON DELETE CASCADE,
    catalog_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('available', 'reserved', 'confirmed', 'cancelled', 'completed')),
    customer_id UUID, -- TODO: Relacionar con leads si existe
    order_id UUID, -- Se relaciona despues
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. COTIZACIONES (QUOTES)
CREATE TABLE IF NOT EXISTS quotes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    customer_id UUID, -- TODO: Relacionar con leads
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('draft', 'sent', 'viewed', 'accepted', 'rejected', 'expired')),
    valid_until TIMESTAMPTZ NOT NULL,
    viewed_at TIMESTAMPTZ,
    accepted_at TIMESTAMPTZ,
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    tax_rate DECIMAL(5,2) DEFAULT 0.00,
    tax_amount DECIMAL(10,2) GENERATED ALWAYS AS (subtotal * tax_rate / 100) STORED,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    total DECIMAL(10,2) GENERATED ALWAYS AS (subtotal + (subtotal * tax_rate / 100) - discount_amount) STORED,
    pdf_url TEXT,
    public_view_token VARCHAR(64) UNIQUE,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quote_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    catalog_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL,
    offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
    description_override TEXT,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price * (1 - discount_percent/100)) STORED,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 6. ÓRDENES UNIVERSALES
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    quote_id UUID REFERENCES quotes(id) ON DELETE SET NULL,
    customer_id UUID, -- TODO: Relacionar con leads
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'confirmed', 'paid', 'processing', 'fulfilled', 'delivered', 'cancelled', 'refunded')),
    subtotal DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    tax_amount DECIMAL(10,2) DEFAULT 0.00,
    discount_amount DECIMAL(10,2) DEFAULT 0.00,
    total_amount DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(20),
    payment_id VARCHAR(255),
    payment_status VARCHAR(20) CHECK (payment_status IN ('pending', 'authorized', 'captured', 'failed', 'refunded')),
    fulfillment_type VARCHAR(20) CHECK (fulfillment_type IN ('shipping', 'digital', 'pickup', 'booking', 'service')),
    scheduled_for TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Corregir FK circular (orders se usa en booking_slots)
ALTER TABLE booking_slots ADD CONSTRAINT fk_booking_slot_order FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE SET NULL;

CREATE TABLE IF NOT EXISTS order_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    order_id UUID REFERENCES orders(id) ON DELETE CASCADE,
    catalog_item_id UUID REFERENCES catalog_items(id) ON DELETE SET NULL,
    offer_id UUID REFERENCES offers(id) ON DELETE SET NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price DECIMAL(10,2) NOT NULL,
    discount_percent DECIMAL(5,2) DEFAULT 0.00,
    subtotal DECIMAL(10,2) GENERATED ALWAYS AS (quantity * unit_price * (1 - discount_percent/100)) STORED,
    fulfillment_status VARCHAR(20) DEFAULT 'pending' CHECK (fulfillment_status IN ('pending', 'processing', 'fulfilled', 'cancelled')),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- 7. ÍNDICES DE RENDIMIENTO
CREATE INDEX IF NOT EXISTS idx_catalog_tenant_type ON catalog_items(tenant_id, type);
CREATE INDEX IF NOT EXISTS idx_catalog_search ON catalog_items USING gin(to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(description, '')));
CREATE INDEX IF NOT EXISTS idx_offers_tenant_valid ON offers(tenant_id, valid_until);
CREATE INDEX IF NOT EXISTS idx_booking_slots_availability ON booking_slots(tenant_id, resource_id, start_time) WHERE status = 'available';
CREATE INDEX IF NOT EXISTS idx_quotes_tenant_status ON quotes(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_quotes_customer_active ON quotes(customer_id) WHERE status IN ('sent', 'viewed');
CREATE INDEX IF NOT EXISTS idx_orders_tenant_status ON orders(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_pending ON orders(payment_status) WHERE payment_status != 'captured';
CREATE INDEX IF NOT EXISTS idx_resources_tenant_type ON resources(tenant_id, type);

-- 8. RLS MULTI-TENANT (Aislamiento Estricto)
ALTER TABLE catalog_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE offers ENABLE ROW LEVEL SECURITY;
ALTER TABLE offer_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE order_items ENABLE ROW LEVEL SECURITY;

-- Políticas estándar
-- Nota: Asegurarse de que el current_setting exista
DO $$ 
DECLARE 
    tbl TEXT;
BEGIN
    FOR tbl IN SELECT tablename FROM pg_tables WHERE schemaname = 'public' AND tablename IN (
        'catalog_items','offers','offer_items','resources','booking_slots','quotes','quote_items','orders','order_items'
    ) LOOP
        -- Omitimos la creacion de politicas de RLS si causan conflicto, es mejor manejarlas segun aplicacion, pero si esta configurado lo hacemos
        BEGIN
            EXECUTE format('CREATE POLICY %I_tenant_isolation ON %I USING (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
            EXECUTE format('CREATE POLICY %I_tenant_insert ON %I FOR INSERT WITH CHECK (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
            EXECUTE format('CREATE POLICY %I_tenant_update ON %I FOR UPDATE USING (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
            EXECUTE format('CREATE POLICY %I_tenant_delete ON %I FOR DELETE USING (tenant_id = current_setting(''app.current_tenant_id'', true)::UUID)', tbl, tbl);
        EXCEPTION WHEN duplicate_object THEN
            NULL;
        END;
    END LOOP;
END $$;

COMMIT;
