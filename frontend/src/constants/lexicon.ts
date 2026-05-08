// =============================================================================
// FLUX LEXICON — Única fuente de verdad para léxico del producto
// FluxAgent OS — Product Grammar Spec (implementación)
// Ref: docs/specs/PRODUCT_GRAMMAR_SPEC.md
// =============================================================================
// ❌ NUNCA usar en UI: chat, bot, crm, settings, ingest, rag, dashboard, admin
// ✅ SIEMPRE usar las constantes de este archivo
// =============================================================================

export const FLUX_LEXICON = {
  // ─── Navegación Principal ─────────────────────────────────────────────────
  OPERATIONS:    "Operaciones",
  INTELLIGENCE:  "Inteligencia",
  WORKFORCE:     "Workforce IA",
  FLOWS:         "Flujos",
  ORGANIZATION:  "Organización",
  ANALYTICS:     "Analítica",
  YANUA:         "Yanua",
  HOME:          "Centro Operativo",
  CONNECTORS:    "Canales",

  // ─── Estados Operacionales ───────────────────────────────────────────────
  HEALTHY:        "Operación Saludable",
  WARNING:        "Riesgo Operativo",
  CRITICAL:       "Bloqueo de Revenue",
  PROCESSING:     "Procesando Inteligencia",
  AUTOMATED:      "Ejecución Autónoma",

  // ─── Workforce IA ────────────────────────────────────────────────────────
  AGENT:          "Agente",
  AGENT_PLURAL:   "Agentes",
  AGENT_ACTIVE:   "Activo",
  AGENT_PAUSED:   "Pausado",
  AGENT_TRAINING: "Entrenando",

  // ─── Inteligencia / RAG ──────────────────────────────────────────────────
  LEARN:    "Aprender",
  PROCESS:  "Procesar",
  VALIDATE: "Validar",
  ASSIGN:   "Asignar",

  // ─── Operaciones / Leads ────────────────────────────────────────────────
  LEAD:           "Lead",
  LEAD_HOT:       "Lead Caliente",
  HANDOFF:        "Intervención Humana",
  CONVERSATION:   "Conversación",
  PIPELINE:       "Pipeline",

  // ─── Microcopy (frases completas para toasts, banners, labels) ──────────
  MICRO: {
    YANUA_RESPONDED:  "Yanua atendió el lead",
    YANUA_ESCALATED:  "Yanua solicitó intervención humana",
    FLOW_EXECUTED:    "El flujo se ejecutó automáticamente",
    FIRST_RESPONSE:   "Yanua atendió su primer lead 🎉",
    FIRST_HOT_LEAD:   "Lead calificado automáticamente 🔥",
    FIRST_HANDOFF:    "Entiende por qué se escaló 👁️",
    FIRST_FLOW:       "Automatización completada ✅",
    AI_PRIORITIZED:   "La IA priorizó esta conversación",
    UPGRADING:        "Desbloqueando priorización IA...",
  },

  // ─── Términos Prohibidos en UI (solo para referencia y ESLint) ───────────
  BLOCKED_TERMS: ["chat", "bot", "crm", "settings", "ingest", "rag", "dashboard", "admin panel"],
} as const;

// Tipo utilitario
export type FluxLexiconKey = keyof typeof FLUX_LEXICON;
