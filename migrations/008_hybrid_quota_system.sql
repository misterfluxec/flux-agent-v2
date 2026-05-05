-- =============================================================================
-- MIGRATION 008: SISTEMA HÍBRIDO DE CUOTAS MULTI-CHANNEL
-- =============================================================================
-- Extiende las tablas existentes (plans, tenants, whatsapp_usage) con soporte
-- para tres modos de operación: global_pool, byoa, hybrid.
-- NO crea tablas nuevas — preserva datos existentes.
-- =============================================================================

-- 1. EXTENDER tabla `plans` con cuotas por canal y configuración de reset
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='plans' AND column_name='cloud_api_quota') THEN
        ALTER TABLE plans
            ADD COLUMN cloud_api_quota       INTEGER DEFAULT 200,
            ADD COLUMN evolution_api_quota   INTEGER DEFAULT 300,
            ADD COLUMN reset_period_days     INTEGER DEFAULT 30,
            ADD COLUMN allow_fallback_to_text BOOLEAN DEFAULT TRUE,
            ADD COLUMN fallback_message      TEXT DEFAULT 'Tu mensaje no pudo ser enviado. Intenta más tarde.';

        RAISE NOTICE '✅ Columnas de cuota añadidas a tabla plans';
    ELSE
        RAISE NOTICE '⏭️ Columnas de cuota en plans ya existen, omitiendo';
    END IF;
END $$;

-- Actualizar cuotas por plan según su categoría
UPDATE plans SET
    cloud_api_quota     = 50,
    evolution_api_quota = 100,
    reset_period_days   = 30
WHERE id = 'starter' AND cloud_api_quota = 200;

UPDATE plans SET
    cloud_api_quota     = 150,
    evolution_api_quota = 350,
    reset_period_days   = 30
WHERE id = 'pro_audio' AND cloud_api_quota = 200;

UPDATE plans SET
    cloud_api_quota     = 400,
    evolution_api_quota = 1600,
    reset_period_days   = 30
WHERE id = 'multimodal' AND cloud_api_quota = 200;

UPDATE plans SET
    cloud_api_quota     = -1,   -- -1 = ilimitado
    evolution_api_quota = -1,
    reset_period_days   = 30
WHERE id = 'premium_human' AND cloud_api_quota = 200;

-- 2. EXTENDER tabla `tenants` con modo de cuota, BYOA y contadores
DO $$
BEGIN
    -- Modo de operación de cuotas
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tenants' AND column_name='quota_mode') THEN
        ALTER TABLE tenants
            ADD COLUMN quota_mode              VARCHAR(20) DEFAULT 'global_pool'
                CHECK (quota_mode IN ('global_pool', 'byoa', 'hybrid')),
            ADD COLUMN preferred_channel       VARCHAR(20) DEFAULT 'evolution_api'
                CHECK (preferred_channel IN ('cloud_api', 'evolution_api')),
            ADD COLUMN auto_fallback_enabled   BOOLEAN DEFAULT TRUE,
            ADD COLUMN is_byoa_enabled         BOOLEAN DEFAULT FALSE;

        RAISE NOTICE '✅ Columnas de modo de cuota añadidas a tenants';
    END IF;

    -- Credenciales BYOA (NULL por defecto)
    -- NOTA DE SEGURIDAD: En MVP se almacenan en texto plano con RLS.
    -- Para producción: setear ENCRYPT_SENSITIVE_DATA=true en .env
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tenants' AND column_name='byoa_cloud_token') THEN
        ALTER TABLE tenants
            ADD COLUMN byoa_cloud_token        TEXT,           -- Token de Meta (sensible)
            ADD COLUMN byoa_phone_number_id    VARCHAR(100),
            ADD COLUMN byoa_waba_id            VARCHAR(100),
            ADD COLUMN byoa_evolution_url      VARCHAR(255),
            ADD COLUMN byoa_evolution_api_key  VARCHAR(100),   -- API Key Evolution (sensible)
            ADD COLUMN admin_whatsapp_number   VARCHAR(20);    -- Para notificaciones de cuota baja

        RAISE NOTICE '✅ Columnas BYOA añadidas a tenants';
    END IF;

    -- Contadores de consumo por canal
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='tenants' AND column_name='used_cloud_api') THEN
        ALTER TABLE tenants
            ADD COLUMN used_cloud_api          INTEGER DEFAULT 0,
            ADD COLUMN used_evolution_api      INTEGER DEFAULT 0,
            ADD COLUMN last_quota_reset_at     TIMESTAMPTZ DEFAULT NOW(),
            ADD COLUMN quota_low_notified_at   TIMESTAMPTZ; -- Evitar spam de notificaciones

        RAISE NOTICE '✅ Contadores de consumo añadidos a tenants';
    END IF;
END $$;

-- 3. EXTENDER tabla `whatsapp_usage` con quota_source y markup
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='whatsapp_usage' AND column_name='quota_source') THEN
        ALTER TABLE whatsapp_usage
            ADD COLUMN quota_source     VARCHAR(20) DEFAULT 'global_pool'
                CHECK (quota_source IN ('global_pool', 'byoa', 'byoa_fallback', 'fallback')),
            ADD COLUMN fluxagent_markup_usd DECIMAL(10,6) DEFAULT 0,
            ADD COLUMN send_status      VARCHAR(20) DEFAULT 'sent'
                CHECK (send_status IN ('sent', 'failed', 'fallback', 'sent_fallback'));

        RAISE NOTICE '✅ Columnas de quota_source añadidas a whatsapp_usage';
    END IF;
END $$;

-- 4. ÍNDICES para reporting de cuotas
CREATE INDEX IF NOT EXISTS idx_tenants_quota_mode ON tenants(quota_mode);
CREATE INDEX IF NOT EXISTS idx_tenants_byoa ON tenants(is_byoa_enabled) WHERE is_byoa_enabled = TRUE;
CREATE INDEX IF NOT EXISTS idx_whatsapp_usage_quota_source ON whatsapp_usage(quota_source, first_message_at);

-- 5. COMENTARIOS de documentación
COMMENT ON COLUMN tenants.quota_mode IS 'Modo de cuotas: global_pool (usa tu pool), byoa (cliente paga directo a Meta), hybrid (pool primero, luego BYOA)';
COMMENT ON COLUMN tenants.byoa_cloud_token IS 'SENSIBLE: Token de acceso de Meta. MVP: texto plano con RLS. Producción: cifrado con ENCRYPT_SENSITIVE_DATA=true';
COMMENT ON COLUMN tenants.byoa_evolution_api_key IS 'SENSIBLE: API Key del servidor Evolution del cliente. MVP: texto plano con RLS.';
COMMENT ON COLUMN tenants.quota_low_notified_at IS 'Timestamp de última notificación de cuota baja. Evita enviar alertas repetidas en el mismo período.';
COMMENT ON COLUMN plans.cloud_api_quota IS 'Conversaciones por período permitidas vía WhatsApp Cloud API (oficial Meta). -1 = ilimitado';
COMMENT ON COLUMN plans.evolution_api_quota IS 'Conversaciones por período permitidas vía Evolution API (no-oficial). -1 = ilimitado';
