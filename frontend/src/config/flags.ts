// =============================================================================
// MATURITY CONFIG — Feature flags por plan de tenant
// FluxAgent OS — Cognitive Flow Spec (implementación)
// Ref: docs/specs/COGNITIVE_FLOW_SPEC.md
// =============================================================================

export type TenantPlan = "starter" | "growth" | "enterprise";

type Feature =
  | "operations"
  | "basic_metrics"
  | "yanua_simple"
  | "one_channel"
  | "lead_scoring"
  | "flows"
  | "sla_tracking"
  | "analytics_advanced"
  | "health_bar_semantic"
  | "health_score_numeric"
  | "recommendations"
  | "explainability"
  | "audit_trail"
  | "policy_editor"
  | "explainability_full"
  | "multi_workforce"
  | "predictive_insights"
  | "compliance_export"
  | "rbac_full";

const STARTER_FEATURES: Feature[] = [
  "operations",
  "basic_metrics",
  "yanua_simple",
  "one_channel",
];

const GROWTH_FEATURES: Feature[] = [
  ...STARTER_FEATURES,
  "lead_scoring",
  "flows",
  "sla_tracking",
  "analytics_advanced",
  "health_bar_semantic",
  "health_score_numeric",
  "recommendations",
  "explainability",
  "compliance_export",
];

const ENTERPRISE_FEATURES: Feature[] = [
  ...GROWTH_FEATURES,
  "audit_trail",
  "policy_editor",
  "explainability_full",
  "multi_workforce",
  "predictive_insights",
  "rbac_full",
];

export const MATURITY_CONFIG: Record<TenantPlan, Feature[]> = {
  starter:    STARTER_FEATURES,
  growth:     GROWTH_FEATURES,
  enterprise: ENTERPRISE_FEATURES,
};

/**
 * Verifica si un plan tiene acceso a un feature determinado.
 * @example hasFeature('growth', 'recommendations') → true
 */
export function hasFeature(plan: TenantPlan, feature: Feature): boolean {
  return MATURITY_CONFIG[plan]?.includes(feature) ?? false;
}

/**
 * Devuelve el plan a partir de un string con fallback seguro.
 */
export function normalizePlan(raw?: string | null): TenantPlan {
  if (raw === "enterprise") return "enterprise";
  if (raw === "growth" || raw === "pro") return "growth";
  return "starter";
}

// ─── Upgrade Prompts (texto de upsell contextual) ───────────────────────────
export const UPGRADE_PROMPTS: Record<Feature, string> = {
  lead_scoring:        "Desbloquea priorización IA automática",
  recommendations:     "Activa insights accionables del sistema",
  explainability:      "Entiende cada decisión de Yanua",
  explainability_full: "Gobernanza IA avanzada con audit trail",
  health_bar_semantic: "Monitoreo operativo en tiempo real",
  health_score_numeric:"Score de salud del negocio (0-100)",
  flows:               "Automatiza secuencias comerciales completas",
  sla_tracking:        "Control de tiempos de respuesta por SLA",
  analytics_advanced:  "Analítica completa con segmentación",
  audit_trail:         "Audit trail completo para compliance",
  policy_editor:       "Editor de políticas de autonomía IA",
  multi_workforce:     "Workforce IA multi-agente colaborativo",
  predictive_insights: "Predicciones de revenue con IA",
  compliance_export:   "Exportación de datos para RGPD/LOPD",
  rbac_full:           "Control de acceso granular por rol",
  // Los siguientes no tienen upsell (son base)
  operations:          "",
  basic_metrics:       "",
  yanua_simple:        "",
  one_channel:         "",
};
