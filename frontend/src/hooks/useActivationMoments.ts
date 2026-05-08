"use client";

import { useState, useEffect } from "react";
import { useEventBus } from "@/providers/EventBusProvider";
import { useTenant } from "@/context/TenantContext";
import { FLUX_LEXICON } from "@/constants/lexicon";
import { TRACK } from "@/lib/telemetry";
import { toast } from "sonner";

// =============================================================================
// USE ACTIVATION MOMENTS — Trackea micro-victorias del tenant
// Persiste en localStorage. Opcional: PATCH /tenants/maturity
// Ref: docs/specs/COGNITIVE_FLOW_SPEC.md
// =============================================================================

type MomentKey = "first_response" | "first_hot_lead" | "first_handoff" | "first_flow";

interface Moment {
  toast: string;
  emoji: string;
  description: string;
}

const MOMENTS: Record<MomentKey, Moment> = {
  first_response: {
    toast:       FLUX_LEXICON.MICRO.FIRST_RESPONSE,
    emoji:       "🎉",
    description: "Tu Workforce IA está operativa",
  },
  first_hot_lead: {
    toast:       FLUX_LEXICON.MICRO.FIRST_HOT_LEAD,
    emoji:       "🔥",
    description: "La IA calificó tu primer oportunidad de venta",
  },
  first_handoff: {
    toast:       FLUX_LEXICON.MICRO.FIRST_HANDOFF,
    emoji:       "👁️",
    description: "El sistema solicitó intervención en el momento correcto",
  },
  first_flow: {
    toast:       FLUX_LEXICON.MICRO.FIRST_FLOW,
    emoji:       "✅",
    description: "Tu primer flujo automatizado se ejecutó sin intervención",
  },
};

export function useActivationMoments() {
  const { history } = useEventBus();
  const { tenantId } = useTenant();
  const [shown, setShown] = useState<Partial<Record<MomentKey, boolean>>>({});

  // ─── Cargar estado desde localStorage ────────────────────────────────────
  useEffect(() => {
    if (!tenantId) return;
    try {
      const stored = JSON.parse(
        localStorage.getItem(`flux:activation:${tenantId}`) || "{}"
      );
      setShown(stored);
    } catch { /* silent */ }
  }, [tenantId]);

  // ─── Persistir y mostrar toast ────────────────────────────────────────────
  const trigger = (key: MomentKey) => {
    if (shown[key] || !tenantId) return;

    const moment = MOMENTS[key];
    const next = { ...shown, [key]: true };
    setShown(next);

    try {
      localStorage.setItem(`flux:activation:${tenantId}`, JSON.stringify(next));
    } catch { /* silent */ }

    // Toast premium
    toast(moment.toast, {
      description: moment.description,
      duration: 5000,
      icon: moment.emoji,
    });

    // Tracking
    switch (key) {
      case "first_response":  TRACK.FIRST_AI_RESPONSE(tenantId);       break;
      case "first_hot_lead":  TRACK.FIRST_HOT_LEAD(tenantId, 0);       break;
      case "first_handoff":   TRACK.FIRST_HANDOFF_VIEWED(tenantId);    break;
      case "first_flow":      TRACK.FIRST_FLOW_EXECUTED(tenantId);     break;
    }

    // Opcional: persistir en backend (fire & forget)
    fetch("/api/v1/tenants/maturity", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ step: `activation.${key}`, completed: true }),
    }).catch(() => {}); // silent fail
  };

  // ─── Escuchar EventBus y disparar momentos ────────────────────────────────
  useEffect(() => {
    if (history.length === 0) return;
    const last = history[history.length - 1];

    if (last.type === "LEAD_HOT"              && !shown.first_hot_lead)  trigger("first_hot_lead");
    if (last.type === "CONVERSATION_HANDOFF"  && !shown.first_handoff)   trigger("first_handoff");
    if (last.type === "FLOW_EXECUTED"         && !shown.first_flow)      trigger("first_flow");
    if (last.type === "AI_RESPONSE_SENT"      && !shown.first_response)  trigger("first_response");
  }, [history]);

  const completedCount = Object.values(shown).filter(Boolean).length;
  const totalMoments = Object.keys(MOMENTS).length;

  return {
    shown,
    trigger,
    completedCount,
    totalMoments,
    allComplete: completedCount === totalMoments,
  };
}
