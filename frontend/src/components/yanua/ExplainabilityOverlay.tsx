"use client";

import { useState } from "react";
import { FLUX_LEXICON } from "@/constants/lexicon";
import { useTenant } from "@/context/TenantContext";
import { hasFeature } from "@/config/flags";
import { TRACK } from "@/lib/telemetry";
import { mockExplain, USE_MOCKS, type ExplanationResponse } from "@/mocks/api";
import { api } from "@/lib/api";
import {
  HelpCircle, X, Loader2, ChevronRight,
  Zap, BookOpen, Shield, BarChart2,
} from "lucide-react";

// =============================================================================
// EXPLAINABILITY OVERLAY — "¿Por qué?"
// Yanua explica sus decisiones en 3 contextos: lead, response, handoff
// Ref: docs/specs/YANUA_GOVERNANCE_SPEC.md
// =============================================================================

export type ExplainContext = "lead" | "response" | "handoff";

interface ExplainabilityOverlayProps {
  context: ExplainContext;
  entityId: string;
  /** Texto del trigger button (opcional) */
  label?: string;
  /** Clase extra para el trigger */
  triggerClassName?: string;
}

const CONTEXT_TITLES: Record<ExplainContext, string> = {
  lead:     "¿Por qué este Lead es 🔥?",
  response: "¿De dónde salió esta respuesta?",
  handoff:  "¿Por qué Yanua solicitó ayuda humana?",
};

export function ExplainabilityOverlay({
  context,
  entityId,
  label,
  triggerClassName,
}: ExplainabilityOverlayProps) {
  const { plan } = useTenant();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ExplanationResponse | null>(null);
  const canExplain = hasFeature(plan, "explainability");

  if (!canExplain) return null;

  const fetch = async () => {
    if (data) { setOpen(true); return; } // cache local

    const t0 = performance.now();
    setLoading(true);
    setOpen(true);
    TRACK.EXPLAIN_OPENED(context, entityId);

    try {
      let result: ExplanationResponse;
      if (USE_MOCKS) {
        result = await mockExplain(context, entityId);
      } else {
        const res = await api.get<ExplanationResponse>(
          `/yana/explain?context=${context}&entity_id=${entityId}`
        );
        result = res.data;
      }
      setData(result);
      TRACK.EXPLAIN_RESPONSE(context, Math.round(performance.now() - t0));
    } catch {
      setData({
        signals: ["No se pudo cargar el razonamiento. Reintenta."],
        policy_applied: "—",
        source: "—",
        confidence_pct: 0,
        reasoning_summary: "Error al consultar el contexto de Yanua.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative inline-block">
      {/* Trigger */}
      <button
        onClick={fetch}
        className={triggerClassName ?? "flex items-center gap-1 text-[11px] text-slate-500 hover:text-cyan-400 transition-colors"}
      >
        <HelpCircle className="h-3 w-3" />
        {label ?? "¿Por qué?"}
      </button>

      {/* Overlay Panel */}
      {open && (
        <>
          {/* Backdrop */}
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />

          {/* Card */}
          <div className="absolute z-50 right-0 mt-2 w-80 bg-slate-950/95 backdrop-blur-2xl border border-white/10 rounded-2xl shadow-2xl shadow-black/60 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200">
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.06]">
              <div className="flex items-center gap-2">
                <div className="h-6 w-6 rounded-lg bg-cyan-500/10 flex items-center justify-center">
                  <Zap className="h-3 w-3 text-cyan-400" />
                </div>
                <span className="text-xs font-bold text-white/70">{FLUX_LEXICON.YANUA}</span>
              </div>
              <button onClick={() => setOpen(false)} className="text-slate-600 hover:text-slate-400 transition-colors">
                <X className="h-3.5 w-3.5" />
              </button>
            </div>

            {/* Title */}
            <div className="px-4 pt-3 pb-2">
              <h4 className="text-[13px] font-bold text-white/80">{CONTEXT_TITLES[context]}</h4>
            </div>

            {/* Content */}
            {loading ? (
              <div className="flex flex-col items-center justify-center py-8 gap-2">
                <Loader2 className="h-5 w-5 text-cyan-400/50 animate-spin" />
                <p className="text-[11px] text-slate-500">{FLUX_LEXICON.YANUA} analizando contexto...</p>
              </div>
            ) : data ? (
              <div className="px-4 pb-4 space-y-3">
                {/* Signals */}
                <div className="space-y-1.5">
                  {data.signals.map((signal, i) => (
                    <div key={i} className="flex items-start gap-2">
                      <ChevronRight className="h-3 w-3 text-cyan-400/50 mt-0.5 shrink-0" />
                      <p className="text-[11px] text-slate-300 leading-relaxed">{signal}</p>
                    </div>
                  ))}
                </div>

                {/* Metadata row */}
                <div className="pt-2 border-t border-white/[0.06] space-y-1.5">
                  <MetaRow icon={Shield} label="Regla aplicada" value={data.policy_applied} color="text-amber-400/70" />
                  <MetaRow icon={BookOpen} label="Fuente" value={data.source} color="text-purple-400/70" />
                  <MetaRow icon={BarChart2} label="Confianza" value={`${data.confidence_pct}%`} color="text-emerald-400/70" />
                </div>

                {/* Summary */}
                {data.reasoning_summary && (
                  <div className="bg-white/[0.03] border border-white/[0.06] rounded-xl p-3">
                    <p className="text-[11px] text-slate-400 leading-relaxed">{data.reasoning_summary}</p>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}

// ─── Meta row sub-component ───────────────────────────────────────────────────
function MetaRow({ icon: Icon, label, value, color }: {
  icon: any; label: string; value: string; color: string;
}) {
  return (
    <div className="flex items-start gap-2">
      <Icon className={cn("h-3 w-3 mt-0.5 shrink-0", color)} />
      <div className="min-w-0">
        <span className="text-[10px] text-slate-600">{label}: </span>
        <span className="text-[11px] text-slate-300">{value}</span>
      </div>
    </div>
  );
}

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}
