-- =============================================================================
-- MIGRATION 006: SEED DE PLANES CON FEATURES MULTIMODALES
-- =============================================================================
-- Agrega los planes base con features JSONB para control de funcionalidades
-- =============================================================================

-- Verificar si ya existen planes
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM plans WHERE id = 'demo_7d') THEN
        INSERT INTO plans (id, nombre, precio, moneda, features, usage_limits, max_agentes, max_instancias_whatsapp, orden, activo) VALUES
        ('demo_7d', 'Demo 7 Días Full', 0.00, 'USD', 
         '{"text":true,"stt":true,"tts":true,"vision":true,"streaming":false,"rag":true,"whatsapp":true}',
         '{"daily_messages":50,"daily_audio_sec":900,"daily_images":10,"monthly_tokens":10000}',
         1, 1, 1, true),
        
        ('starter', 'Starter', 0.00, 'USD',
         '{"text":true,"stt":false,"tts":false,"vision":false,"streaming":false,"rag":true,"whatsapp":true}',
         '{"daily_messages":100,"daily_audio_sec":0,"daily_images":0,"monthly_tokens":5000}',
         1, 1, 2, true),
        
        ('pro_audio', 'Agente Escucha', 9.99, 'USD',
         '{"text":true,"stt":true,"tts":false,"vision":false,"streaming":false,"rag":true,"whatsapp":true}',
         '{"daily_messages":500,"daily_audio_sec":1800,"daily_images":0,"monthly_tokens":25000}',
         2, 2, 3, true),
        
        ('multimodal', 'Agente Multimodal', 19.99, 'USD',
         '{"text":true,"stt":true,"tts":true,"vision":true,"streaming":false,"rag":true,"whatsapp":true}',
         '{"daily_messages":2000,"daily_audio_sec":3600,"daily_images":50,"monthly_tokens":100000}',
         5, 5, 4, true),
        
        ('premium_human', 'Flux Human Pro', 49.99, 'USD',
         '{"text":true,"stt":true,"tts":true,"vision":true,"streaming":true,"rag":true,"whatsapp":true,"analytics":true,"custom_llm":true}',
         '{"daily_messages":-1,"daily_audio_sec":-1,"daily_images":-1,"monthly_tokens":-1}',
         -1, -1, 5, true);
        
        RAISE NOTICE 'Planes seeded correctamente';
    ELSE
        RAISE NOTICE 'Los planes ya existen, omitiendo seed';
    END IF;
END $$;

-- Actualizar tenants existentes para asignar features según su plan actual
UPDATE tenants 
SET features = 
    CASE plan
        WHEN 'starter' THEN '{"text":true,"stt":false,"tts":false,"vision":false,"streaming":false,"rag":true,"whatsapp":true}'
        WHEN 'pro' THEN '{"text":true,"stt":true,"tts":false,"vision":false,"streaming":false,"rag":true,"whatsapp":true}'
        WHEN 'business' THEN '{"text":true,"stt":true,"tts":true,"vision":true,"streaming":false,"rag":true,"whatsapp":true}'
        WHEN 'enterprise' THEN '{"text":true,"stt":true,"tts":true,"vision":true,"streaming":true,"rag":true,"whatsapp":true,"analytics":true,"custom_llm":true}'
        ELSE '{"text":true,"stt":false,"tts":false,"vision":false,"streaming":false,"rag":false,"whatsapp":false}'
    END,
    usage_limits = 
    CASE plan
        WHEN 'starter' THEN '{"daily_messages":100,"daily_audio_sec":0,"daily_images":0}'
        WHEN 'pro' THEN '{"daily_messages":500,"daily_audio_sec":1800,"daily_images":0}'
        WHEN 'business' THEN '{"daily_messages":2000,"daily_audio_sec":3600,"daily_images":50}'
        WHEN 'enterprise' THEN '{"daily_messages":-1,"daily_audio_sec":-1,"daily_images":-1}'
        ELSE '{"daily_messages":50,"daily_audio_sec":0,"daily_images":0}'
    END
WHERE features IS NULL OR usage_limits IS NULL;

-- Agregar columnas de features y usage_limits a tenants si no existen
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tenants' AND column_name = 'features') THEN
        ALTER TABLE tenants ADD COLUMN features JSONB NOT NULL DEFAULT '{}';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'tenants' AND column_name = 'usage_limits') THEN
        ALTER TABLE tenants ADD COLUMN usage_limits JSONB NOT NULL DEFAULT '{}';
    END IF;
END $$;

COMMENT ON COLUMN tenants.features IS 'Features habilitados por plan: text, stt, tts, vision, streaming, rag, whatsapp, analytics, custom_llm';
COMMENT ON COLUMN tenants.usage_limits IS 'Límites de uso: daily_messages, daily_audio_sec, daily_images, monthly_tokens (-1 = ilimitado)';