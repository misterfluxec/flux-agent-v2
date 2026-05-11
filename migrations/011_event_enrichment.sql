-- =============================================================================
-- MIGRATION 011: EVENT ENRICHMENT
-- ACK State, Ownership, Priority Score, Tags
-- =============================================================================
-- Estos 4 campos convierten el event_log en una cola de trabajo operacional
-- real, no solo un log de auditoría. Son la diferencia entre "ver qué pasó"
-- y "gestionar qué está pasando".
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. ACK State: ciclo de vida de atención del evento
-- -----------------------------------------------------------------------------
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_ack_state') THEN
        CREATE TYPE event_ack_state AS ENUM (
            'unresolved',    -- Nuevo, sin atención (default)
            'acknowledged',  -- Visto por un operador
            'snoozed',       -- Pospuesto intencionalmente
            'resolved'       -- Cerrado/completado
        );
        RAISE NOTICE '✅ ENUM event_ack_state creado';
    END IF;
END $$;

ALTER TABLE event_log
    ADD COLUMN IF NOT EXISTS ack_state event_ack_state DEFAULT 'unresolved',
    ADD COLUMN IF NOT EXISTS acked_by UUID,          -- FK a users.id (quien lo atendió)
    ADD COLUMN IF NOT EXISTS acked_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS snooze_until TIMESTAMPTZ, -- Para "snoozed": cuándo re-aparece
    ADD COLUMN IF NOT EXISTS resolved_at TIMESTAMPTZ;

-- -----------------------------------------------------------------------------
-- 2. Ownership / Assignment: responsabilidad operacional
-- -----------------------------------------------------------------------------
ALTER TABLE event_log
    ADD COLUMN IF NOT EXISTS assigned_to UUID,       -- FK a users.id
    ADD COLUMN IF NOT EXISTS assigned_team VARCHAR(100),
    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ;

-- -----------------------------------------------------------------------------
-- 3. Priority Score Numérico (0-100)
-- Calculado por SeverityEngine. Permite sorting continuo, AI ranking, queues.
-- -----------------------------------------------------------------------------
ALTER TABLE event_log
    ADD COLUMN IF NOT EXISTS priority_score SMALLINT DEFAULT 0
        CONSTRAINT priority_score_range CHECK (priority_score BETWEEN 0 AND 100);

-- -----------------------------------------------------------------------------
-- 4. Event Tags: filtrado, búsqueda, automations
-- Array de strings — simple, flexible, indexado con GIN.
-- -----------------------------------------------------------------------------
ALTER TABLE event_log
    ADD COLUMN IF NOT EXISTS tags TEXT[] DEFAULT '{}';

-- -----------------------------------------------------------------------------
-- Índices nuevos para las consultas del dashboard
-- -----------------------------------------------------------------------------

-- Priority Queue: eventos de alta prioridad sin atender
CREATE INDEX IF NOT EXISTS idx_event_log_priority_queue
    ON event_log (tenant_id, priority_score DESC, occurred_at DESC)
    WHERE ack_state = 'unresolved';

-- Assigned work: eventos asignados a un usuario
CREATE INDEX IF NOT EXISTS idx_event_log_assigned
    ON event_log (assigned_to, ack_state)
    WHERE assigned_to IS NOT NULL;

-- Tags: búsqueda con GIN (soporta @> "contiene tag")
CREATE INDEX IF NOT EXISTS idx_event_log_tags
    ON event_log USING GIN (tags);

-- ACK state: filtro rápido para la queue
CREATE INDEX IF NOT EXISTS idx_event_log_ack_state
    ON event_log (tenant_id, ack_state, occurred_at DESC);

-- Snooze: cron para re-activar eventos pospuestos
CREATE INDEX IF NOT EXISTS idx_event_log_snooze
    ON event_log (snooze_until)
    WHERE ack_state = 'snoozed' AND snooze_until IS NOT NULL;
