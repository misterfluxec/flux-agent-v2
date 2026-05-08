"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { usePathname } from "next/navigation";
import { useTenant } from "@/context/TenantContext";
import { hasFeature } from "@/config/flags";
import { TRACK } from "@/lib/telemetry";
import { mockRecommendations, USE_MOCKS, type Insight } from "@/mocks/api";
import { api } from "@/lib/api";
import { useEventBus } from "@/providers/EventBusProvider";
import {
  Flame, Brain, TrendingUp, CheckSquare,
  X, ChevronRight, Sparkles,
} from "lucide-react";

// =============================================================================
// RECOMMENDATION CARD — Decision Center
// Insights accionables basados en EventBus + backend
// Ref: docs/specs/COGNITIVE_FLOW_SPEC.md
// =============================================================================

const TYPE_CONFIG = {
  hot_lead:    { icon: Flame,       color: "text-red-400",    bg: "bg-red-500/[0.06]",    border: "border-red-500/15"   },
  ia_gap:      { icon: Brain,       color: "text-amber-400",  bg: "bg-amber-500/[0.06]",  border: "border-amber-500/15" },
  performance: { icon: TrendingUp,  color: "text-cyan-400",   bg: "bg-cyan-500/[0.06]",   border: "border-cyan-500/15"  },
  task:        { icon: CheckSquare, color: "text-emerald-400",bg: "bg-emerald-500/[0.06]",border: "border-emerald-500/15"},
} as const;

interface RecommendationCardProps {
  insight: Insight;
  onDismiss: (id: string) => void;
}

function RecommendationCard({ insight, onDismiss }: RecommendationCardProps) {
  const router = useRouter();
  const pathname = usePathname();
  const locale = pathname?.split("/")[1] || "es";
  const cfg = TYPE_CONFIG[insight.type];
  const Icon = cfg.icon;

  const handleAction = (action: Insight["actions"][number]) => {
    if (action.variant === "dismiss") {
      TRACK.RECOMMENDATION_DISMISSED(insight.type);
      onDismiss(insight.id);
      return;
    }
    TRACK.RECOMMENDATION_APPLIED(insight.type);
    if (action.href) router.push(`/${locale}${action.href}`);
  };

  return (
    <div className={`rounded-xl border p-4 ${cfg.bg} ${cfg.border} flex flex-col gap-3 transition-all`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-start gap-2.5">
          <div className={`h-7 w-7 rounded-lg bg-white/5 flex items-center justify-center shrink-0 mt-0.5`}>
            <Icon className={`h-3.5 w-3.5 ${cfg.color}`} />
          </div>
          <div>
            <p className="text-[13px] font-bold text-white/75 leading-snug">{insight.title}</p>
            <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">{insight.context}</p>
          </div>
        </div>
        <button onClick={() => { TRACK.RECOMMENDATION_DISMISSED(insight.type); onDismiss(insight.id); }}
          className="text-slate-600 hover:text-slate-400 shrink-0 transition-colors mt-0.5">
          <X className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="flex flex-wrap gap-2">
        {insight.actions.map(action => (
          <button key={action.label} onClick={() => handleAction(action)}
            className={`text-[11px] font-semibold px-3 py-1.5 rounded-lg flex items-center gap-1 transition-all ${
              action.variant === "primary"
                ? `${cfg.bg} ${cfg.color} hover:brightness-125 border ${cfg.border}`
                : action.variant === "dismiss"
                ? "text-slate-600 hover:text-slate-400"
                : "bg-white/[0.04] text-slate-400 hover:bg-white/[0.07] border border-white/[0.05]"
            }`}>
            {action.label}
            {action.variant === "primary" && <ChevronRight className="h-3 w-3" />}
          </button>
        ))}
      </div>
    </div>
  );
}

// =============================================================================
// RECOMMENDATION FEED — Contenedor de insights en Home
// =============================================================================

export function RecommendationFeed() {
  const { plan, tenantId } = useTenant();
  const { history } = useEventBus();
  const [insights, setInsights] = useState<Insight[]>([]);
  const [dismissed, setDismissed] = useState<Set<string>>(new Set());
  const [loaded, setLoaded] = useState(false);

  const canSeeRecommendations = hasFeature(plan, "recommendations");

  useEffect(() => {
    if (!canSeeRecommendations) return;
    (async () => {
      try {
        let data: Insight[];
        if (USE_MOCKS) {
          data = await mockRecommendations();
        } else {
          const res = await api.get<Insight[]>("/insights/recommendations");
          data = res.data;
        }
        setInsights(data);
      } catch { /* silent */ }
      finally { setLoaded(true); }
    })();
  }, [canSeeRecommendations]);

  // Añadir insights reactivos desde EventBus
  useEffect(() => {
    if (!canSeeRecommendations) return;
    const lastEvent = history[history.length - 1];
    if (!lastEvent) return;

    if (lastEvent.type === "LEAD_HOT") {
      const newInsight: Insight = {
        id: `eb_hot_${Date.now()}`,
        type: "hot_lead",
        title: `Lead caliente detectado 🔥`,
        context: `Score ${lastEvent.data?.score ?? "alto"} — requiere atención inmediata.`,
        priority: "high",
        actions: [
          { label: "🔥 Ver Operaciones", variant: "primary", href: "/dashboard/conversations" },
          { label: "Ignorar", variant: "dismiss" },
        ],
      };
      setInsights(prev => [newInsight, ...prev.filter(i => i.id !== newInsight.id)]);
    }
  }, [history, canSeeRecommendations]);

  const visible = insights.filter(i => !dismissed.has(i.id));
  if (!canSeeRecommendations || (!loaded && visible.length === 0)) return null;

  return (
    <div className="space-y-3">
      {/* Header */}
      <div className="flex items-center gap-2">
        <Sparkles className="h-3.5 w-3.5 text-cyan-400/50" />
        <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">
          Yanua recomienda
        </h3>
      </div>

      {visible.length === 0 ? (
        <div className="text-[11px] text-slate-600 py-2">Sin recomendaciones activas — operación fluida ✓</div>
      ) : (
        <div className="grid gap-2">
          {visible.map(insight => (
            <RecommendationCard
              key={insight.id}
              insight={insight}
              onDismiss={id => setDismissed(prev => new Set([...prev, id]))}
            />
          ))}
        </div>
      )}
    </div>
  );
}
