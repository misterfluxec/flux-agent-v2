-- =============================================================================
-- MIGRACIÓN 013: CORRECCIÓN DE ESQUEMA DE AGENTS - FLUXAGENT V2
-- =============================================================================
-- Objetivo: Agregar columnas faltantes con valores por defecto seguros
-- Impacto: Desbloquea onboarding completo de agentes sin errores
-- Ejecución: Idempotente (seguro ejecutar múltiples veces)
-- Rollback: No requerido (ADD COLUMN IF NOT EXISTS + UPDATE condicional)
-- =============================================================================

BEGIN;

-- -----------------------------------------------------------------------------
-- 1. AGREGAR COLUMNAS FALTANTES CON IF NOT EXISTS (seguro para re-ejecución)
-- -----------------------------------------------------------------------------

-- script_ventas: JSONB con estructura completa para scripts de venta
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS script_ventas JSONB 
DEFAULT '{"fases": [], "reglas": [], "scripts": [], "escalacion": {"enabled": true, "keywords": []}}'::jsonb;

-- agent_type: String con default 'sales' para compatibilidad con frontend
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS agent_type VARCHAR(50) 
DEFAULT 'sales';

-- system_prompt: TEXT con fallback inteligente a personalidad/instrucciones
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS system_prompt TEXT 
DEFAULT 'Eres un asistente profesional.';

-- specialty: Especialidad del agente para enrutamiento y personalización
ALTER TABLE agents 
ADD COLUMN IF NOT EXISTS specialty VARCHAR(100) 
DEFAULT 'general';

-- -----------------------------------------------------------------------------
-- 2. ACTUALIZAR REGISTROS EXISTENTES (solo NULL/vacíos, preservar datos)
-- -----------------------------------------------------------------------------

UPDATE agents 
SET 
  script_ventas = CASE 
    WHEN script_ventas IS NULL 
      OR script_ventas = 'null'::jsonb 
      OR script_ventas = '{}'::jsonb
    THEN '{"fases": [], "reglas": [], "scripts": [], "escalacion": {"enabled": true, "keywords": []}}'::jsonb
    ELSE script_ventas 
  END,
  agent_type = CASE 
    WHEN agent_type IS NULL OR agent_type = '' THEN 'sales'
    ELSE agent_type 
  END,
  system_prompt = CASE 
    WHEN system_prompt IS NULL OR system_prompt = '' 
    THEN COALESCE(personalidad, instrucciones, 'Eres un asistente profesional.')
    ELSE system_prompt 
  END,
  specialty = CASE 
    WHEN specialty IS NULL OR specialty = '' 
    THEN COALESCE(tipo_negocio, 'general')
    ELSE specialty 
  END
WHERE id IS NOT NULL;

-- -----------------------------------------------------------------------------
-- 3. ÍNDICES PARA PERFORMANCE (queries frecuentes del frontend)
-- -----------------------------------------------------------------------------

-- Filtrado por tipo de agente (usado en dropdowns y filtros)
CREATE INDEX IF NOT EXISTS idx_agents_agent_type ON agents(agent_type);

-- Búsquedas dentro de JSONB: scripts, reglas, keywords de escalación
CREATE INDEX IF NOT EXISTS idx_agents_script_ventas ON agents USING GIN(script_ventas);

-- Query compuesto: tenant + tipo + estado (listado de agentes por usuario)
CREATE INDEX IF NOT EXISTS idx_agents_tenant_type_status 
ON agents(tenant_id, agent_type, estado);

-- -----------------------------------------------------------------------------
-- 4. DOCUMENTACIÓN EN BASE DE DATOS (para futuros desarrolladores)
-- -----------------------------------------------------------------------------

COMMENT ON COLUMN agents.script_ventas IS 'Estructura JSON de scripts de venta: fases, reglas, scripts y configuración de escalación automática';
COMMENT ON COLUMN agents.agent_type IS 'Tipo de agente: sales, support, bookings, custom - define comportamiento base';
COMMENT ON COLUMN agents.system_prompt IS 'Prompt principal del sistema: combina instrucciones, personalidad y reglas de comportamiento';
COMMENT ON COLUMN agents.specialty IS 'Especialidad del agente para enrutamiento inteligente y personalización de respuestas';

-- -----------------------------------------------------------------------------
-- 5. VALIDACIÓN AUTOMÁTICA POST-MIGRACIÓN (QA integrado)
-- -----------------------------------------------------------------------------

DO $$
DECLARE
  null_count INTEGER;
  total_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO total_count FROM agents;
  
  SELECT COUNT(*) INTO null_count 
  FROM agents 
  WHERE script_ventas IS NULL 
     OR agent_type IS NULL 
     OR system_prompt IS NULL;
  
  IF null_count > 0 THEN
    RAISE WARNING '⚠️  ALERTA: % de % agentes tienen valores NULL críticos', null_count, total_count;
    RAISE NOTICE '💡 Ejecutar manualmente: SELECT id, nombre FROM agents WHERE script_ventas IS NULL;';
  ELSE
    RAISE NOTICE '✅ MIGRACIÓN EXITOSA: % agentes validados con valores completos', total_count;
  END IF;
END $$;

-- -----------------------------------------------------------------------------
-- 6. VALIDAR ESTRUCTURA FINAL
-- -----------------------------------------------------------------------------

SELECT 
  column_name, 
  data_type, 
  is_nullable, 
  column_default
FROM information_schema.columns 
WHERE table_name = 'agents' 
  AND column_name IN ('script_ventas', 'agent_type', 'system_prompt', 'specialty')
ORDER BY column_name;

-- Conteo de registros actualizados
SELECT 
  COUNT(*) as total_agents,
  COUNT(CASE WHEN script_ventas IS NOT NULL THEN 1 END) as with_script_ventas,
  COUNT(CASE WHEN agent_type IS NOT NULL THEN 1 END) as with_agent_type,
  COUNT(CASE WHEN system_prompt IS NOT NULL THEN 1 END) as with_system_prompt,
  COUNT(CASE WHEN specialty IS NOT NULL THEN 1 END) as with_specialty
FROM agents;

-- Establecer comentario en la tabla
COMMENT ON TABLE agents IS 'Agentes IA con schema completo para onboarding funcional';
