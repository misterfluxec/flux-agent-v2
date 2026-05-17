import { TenantPlan } from "./flags";

export type UserRole = "admin" | "operator" | "viewer" | "owner";
export type RiskLevel = "low" | "medium" | "critical";

export interface CapabilityConfig {
  minPlan: TenantPlan;
  roles?: UserRole[]; // Roles explícitos requeridos
  risk?: RiskLevel;
  requiresMFA?: boolean;
}

// ─── Capability Manifest ──────────────────────────────────────────────────
// Define las reglas de acceso centralizadas para toda la aplicación
export const CAPABILITIES: Record<string, CapabilityConfig> = {
  // Navegación y vista (low risk)
  "ai.recommendations.view": { minPlan: "growth", risk: "low" },
  "system.analytics.advanced": { minPlan: "growth", risk: "low" },
  "system.predictive_insights.view": { minPlan: "enterprise", risk: "low" },
  
  // Comercio — vistas (low risk)
  "commerce.catalog.view": { minPlan: "starter", risk: "low" },
  "commerce.quotes.view": { minPlan: "starter", risk: "low" },
  "commerce.orders.view": { minPlan: "starter", risk: "low" },
  
  // Comercio — acciones (medium risk)
  "commerce.catalog.edit": { minPlan: "growth", roles: ["admin", "operator", "owner"], risk: "medium" },
  "commerce.quotes.approve": { minPlan: "growth", roles: ["admin", "owner"], risk: "medium" },
  "commerce.orders.create": { minPlan: "growth", roles: ["admin", "operator", "owner"], risk: "medium" },
  
  // Comercio — acciones críticas (critical risk)
  "commerce.catalog.import": { minPlan: "enterprise", roles: ["admin", "owner"], risk: "critical" },
  "commerce.orders.refund": { minPlan: "enterprise", roles: ["admin", "owner"], risk: "critical", requiresMFA: true },

  // Exportación y manipulación masiva (medium risk)
  "system.analytics.export": { minPlan: "growth", roles: ["admin", "owner"], risk: "medium" },
  "compliance.audit_trail.view": { minPlan: "enterprise", roles: ["admin", "owner"], risk: "medium" },

  // Acciones operacionales críticas (critical risk)
  "inventory.override.execute": { minPlan: "enterprise", roles: ["admin", "owner"], risk: "critical", requiresMFA: true },
  "ai.policy_editor.execute": { minPlan: "enterprise", roles: ["admin", "owner"], risk: "critical" },
  "system.rbac.manage": { minPlan: "enterprise", roles: ["owner"], risk: "critical" },
};

const PLAN_WEIGHTS: Record<TenantPlan, number> = {
  starter: 1,
  growth: 2,
  enterprise: 3,
};

// ─── Capability Policy Engine ─────────────────────────────────────────────

export interface PolicyContext {
  plan: TenantPlan;
  role?: UserRole;
  // future: hasMFA?: boolean;
}

/**
 * Motor puro que evalúa si un contexto tiene acceso a una capacidad.
 * Retorna true si tiene acceso, false si no.
 */
export function canAccess(capabilityId: string, context: PolicyContext): boolean {
  const cap = CAPABILITIES[capabilityId];
  
  // Si la capacidad no está definida en el manifiesto, por seguridad la denegamos
  if (!cap) {
    console.warn(`[PolicyEngine] Capacidad no registrada: ${capabilityId}`);
    return false;
  }

  // 1. Evaluar jerarquía de planes
  const userPlanWeight = PLAN_WEIGHTS[context.plan] || 0;
  const requiredPlanWeight = PLAN_WEIGHTS[cap.minPlan] || 99;
  
  if (userPlanWeight < requiredPlanWeight) {
    return false;
  }

  // 2. Evaluar Roles (si la capacidad exige roles específicos)
  if (cap.roles && cap.roles.length > 0) {
    if (!context.role) return false;
    if (!cap.roles.includes(context.role)) {
      return false;
    }
  }

  // 3. Futuras evaluaciones (MFA, Entorno, etc.) pueden ir aquí

  return true;
}

// ─── Textos de Upsell Centralizados ───────────────────────────────────────
// Mensajes de marketing para cuando behavior === "upsell"
export const CAPABILITY_UPSELL_PROMPTS: Record<string, string> = {
  "ai.recommendations.view": "Activa insights accionables del sistema",
  "system.analytics.advanced": "Analítica completa con segmentación",
  "system.predictive_insights.view": "Predicciones de revenue con IA",
  "system.analytics.export": "Exportación avanzada para reporting",
  "compliance.audit_trail.view": "Gobernanza avanzada con audit trail",
  "ai.policy_editor.execute": "Editor de políticas de autonomía IA",
  "system.rbac.manage": "Control de acceso granular por role",
};
