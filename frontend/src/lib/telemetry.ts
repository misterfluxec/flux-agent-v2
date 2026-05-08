// =============================================================================
// TELEMETRY — Wrapper de analytics/tracking para Beta KPIs
// Usa PostHog / Mixpanel en prod, console.log en dev
// =============================================================================

type TrackProps = Record<string, string | number | boolean | null | undefined>;

/**
 * Trackea un evento de producto.
 * En producción, enviar a PostHog / Mixpanel.
 * En desarrollo, solo loguear.
 */
export function trackEvent(event: string, props?: TrackProps): void {
  if (typeof window === "undefined") return;

  if (process.env.NODE_ENV === "production") {
    // PostHog integration (descomentar cuando esté configurado)
    // window.posthog?.capture(event, props);

    // Mixpanel integration (descomentar cuando esté configurado)
    // window.mixpanel?.track(event, props);

    // Fallback: send to our own analytics endpoint
    fetch("/api/v1/analytics/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ event, properties: props, timestamp: new Date().toISOString() }),
    }).catch(() => {}); // Silent fail — never block UX
  } else {
    console.log(`[📊 TRACK] ${event}`, props ?? "");
  }
}

// ─── Eventos de Beta KPIs ────────────────────────────────────────────────────
export const TRACK = {
  // Activation Moments
  FIRST_AI_RESPONSE:    (tenantId: string) => trackEvent("activation.first_response", { tenant_id: tenantId }),
  FIRST_HOT_LEAD:       (tenantId: string, score: number) => trackEvent("activation.first_hot_lead", { tenant_id: tenantId, score }),
  FIRST_HANDOFF_VIEWED: (tenantId: string) => trackEvent("activation.first_explain", { tenant_id: tenantId }),
  FIRST_FLOW_EXECUTED:  (tenantId: string) => trackEvent("activation.first_flow", { tenant_id: tenantId }),

  // Health Bar
  HEALTH_CRITICAL_SEEN: (score: number) => trackEvent("health_bar.critical_seen", { score }),
  HEALTH_EXPANDED:      () => trackEvent("health_bar.expanded"),

  // Explainability
  EXPLAIN_OPENED:   (context: string, entityId: string) => trackEvent("explain.opened", { context, entity_id: entityId }),
  EXPLAIN_RESPONSE: (context: string, latencyMs: number) => trackEvent("explain.response", { context, latency_ms: latencyMs }),

  // Recommendations
  RECOMMENDATION_APPLIED:   (type: string) => trackEvent("recommendation.applied", { type }),
  RECOMMENDATION_DISMISSED: (type: string) => trackEvent("recommendation.dismissed", { type }),

  // Onboarding
  ONBOARDING_STEP_COMPLETE: (step: string) => trackEvent("onboarding.step_complete", { step }),
  ONBOARDING_DISMISSED:     () => trackEvent("onboarding.dismissed"),

  // Upgrade
  UPGRADE_PROMPTED: (feature: string, plan: string) => trackEvent("upgrade.prompted", { feature, current_plan: plan }),
  UPGRADE_CLICKED:  (feature: string) => trackEvent("upgrade.clicked", { feature }),

  // Compliance
  EXPORT_DOWNLOADED: (type: string) => trackEvent("compliance.export", { type }),
};
