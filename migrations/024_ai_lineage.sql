-- Migration 024: AI Decision Lineage & Feedback Loop
-- Fase 4C.4: Refinamientos Enterprise

-- 1. AI Decision Lineage (Hashing)
ALTER TABLE ai_response_audit_log
ADD COLUMN IF NOT EXISTS context_hash VARCHAR(64),          -- SHA-256 del payload exacto enviado al LLM
ADD COLUMN IF NOT EXISTS derived_chain_hash VARCHAR(64);    -- SHA-256 de las dependencias operacionales

-- 2. Recommendation Feedback Loop
-- Permitirá guardar: USEFUL, INCORRECT, INCOMPLETE
ALTER TABLE ai_response_audit_log
ADD COLUMN IF NOT EXISTS operator_feedback VARCHAR(50),
ADD COLUMN IF NOT EXISTS feedback_reason TEXT,
ADD COLUMN IF NOT EXISTS feedback_given_at TIMESTAMP WITH TIME ZONE;
