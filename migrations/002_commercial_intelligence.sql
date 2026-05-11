-- ==========================================
-- FLUXAGENT V2 — PHASE 2: COMMERCIAL INTELLIGENCE CORE
-- Ejecutar en: PostgreSQL 14+
-- Evolución de catalog_items -> business_offers
-- ==========================================

BEGIN;

-- 1. Renombrar la tabla principal para reflejar el nuevo paradigma
ALTER TABLE catalog_items RENAME TO business_offers;

-- 2. Añadir nuevas columnas HÍBRIDAS (Columnas reales + JSONB para IA)
ALTER TABLE business_offers 
ADD COLUMN is_active BOOLEAN DEFAULT true,
ADD COLUMN fulfillment_type VARCHAR(20) DEFAULT 'digital' CHECK (fulfillment_type IN ('shipping', 'digital', 'appointment', 'pickup')),
ADD COLUMN sales_playbook JSONB DEFAULT '{"positioning": "", "ideal_customer": [], "objection_handling": [], "urgency_triggers": [], "closing_style": "consultative"}'::jsonb,
ADD COLUMN commercial_strategy JSONB DEFAULT '{"upsells": [], "cross_sells": [], "downsells": [], "fallback_offer": null}'::jsonb,
ADD COLUMN pricing_rules JSONB DEFAULT '{}'::jsonb,
ADD COLUMN availability_rules JSONB DEFAULT '{}'::jsonb;

-- 3. Renombrar referencias en otras tablas (Foreign Keys)
-- Nota: PostgreSQL maneja las dependencias FK automáticamente tras el RENAME, 
-- pero las columnas se llaman catalog_item_id. Vamos a renombrarlas a business_offer_id.

ALTER TABLE offers RENAME COLUMN catalog_item_id TO business_offer_id;
ALTER TABLE offer_items RENAME COLUMN catalog_item_id TO business_offer_id;
ALTER TABLE booking_slots RENAME COLUMN catalog_item_id TO business_offer_id;
ALTER TABLE quote_items RENAME COLUMN catalog_item_id TO business_offer_id;
ALTER TABLE order_items RENAME COLUMN catalog_item_id TO business_offer_id;

-- 4. Vistas Operacionales (Materializadas o Simples)
-- Opcional: Crear una vista que unifique leads y quotes para el panel de "Ventas" (Pipeline)
CREATE OR REPLACE VIEW vw_sales_pipeline AS
SELECT 
    q.id as entity_id,
    'quote' as entity_type,
    q.tenant_id,
    q.customer_id,
    q.status,
    q.total as amount,
    q.updated_at
FROM quotes q
WHERE q.status NOT IN ('expired', 'rejected');

-- 5. Actualizar políticas RLS
-- Como renombramos la tabla, las políticas deberían migrar solas, pero aseguramos la nueva sintaxis:
DROP POLICY IF EXISTS catalog_items_tenant_isolation ON business_offers;
CREATE POLICY business_offers_tenant_isolation ON business_offers USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID);

COMMIT;
