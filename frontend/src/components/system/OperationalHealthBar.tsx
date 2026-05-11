"use client";

import { useEffect, useState } from "react";
import { useEventBus } from "@/providers/EventBusProvider";
import { fetchHealth } from "@/lib/api";
import { api } from "@/lib/api";
import { useTenant } from "@/context/TenantContext";
import { hasFeature } from "@/config/flags";
import { FLUX_LEXICON } from "@/constants/lexicon";
import { TRACK } from "@/lib/telemetry";
import {
  Activity, Wifi, WifiOff, Bot, MessageSquare,
  AlertTriangle, CheckCircle2, ChevronDown, Clock,
} from "lucide-react";
import { cn } from "@/lib/utils";

// =============================================================================
// OPERATIONAL HEALTH BAR — Fórmula 40/40/20
// Infra (40%) + Operación (40%) + Negocio (20%) = Score 0-100
// Ref: docs/specs/OPERATIONAL_STATE_SPEC.md
// =============================================================================

type HealthStatus = "healthy" | "warning" | "critical" | "processing";

interface CompositeHealth {
  status: HealthStatus;
  score: number;               // 0-100 compuesto
  infraScore: number;          // 0-100
  opsScore: number;            // 0-100
  bizScore: number;            // 0-100
  channels: { connected: number; total: number };
  ia: { status: "ok" | "slow" | "down"; latencyMs?: number };
  handoffs: number;
  slaAvgMin?: number;
  aiConfidence?: number;
}

const INITIAL: CompositeHealth = {
  status: "healthy",
  score: 100,
  infraScore: 100,
  opsScore: 100,
  bizScore: 100,
  channels: { connected: 1, total: 1 },
  ia: { status: "ok" },
  handoffs: 0,
};

export function OperationalHealthBar() {
  const { isConnected, history } = useEventBus();
  const { plan } = useTenant();
  const [health, setHealth] = useState<CompositeHealth>(INITIAL);
  const [expanded, setExpanded] = useState(false);
  const showNumericScore = hasFeature(plan, "health_score_numeric");

  // ─── Polling + Fórmula 40/40/20 ─────────────────────────────────────────
  useEffect(() => {
    const compute = async () => {
      // Guard: no API calls without token (avoids 401 storm on public pages)
      const token = typeof window !== "undefined" ? localStorage.getItem("flux_token") : null;
      if (!token) return;

      try {
        // 1. Infra (40%) — desde /health existente + resilience
        const infraData = await fetchHealth();
        const services = infraData.servicios || {};

        const channelEntries = Object.entries(services).filter(
          ([k]) => k.includes("whatsapp") || k.includes("telegram") || k.includes("evolution")
        );
        const connectedCh = channelEntries.filter(
          ([, v]: any) => v.estado === "conectado" || v.estado === "saludable"
        ).length;

        const ollamaService: any = services["ollama"] || services["ai"] || {};
        const iaLatency = ollamaService.latencia_ms;
        const iaStatus: "ok" | "slow" | "down" =
          ollamaService.estado === "saludable"
            ? iaLatency && iaLatency > 1500 ? "slow" : "ok"
            : "down";

        // Infra score: canales + IA + conexión EventBus
        const channelScore = channelEntries.length > 0
          ? (connectedCh / channelEntries.length) * 100 : 100;
        const iaScore = iaStatus === "ok" ? 100 : iaStatus === "slow" ? 65 : 0;
        const ebScore = isConnected ? 100 : 30;
        const infraScore = Math.round((channelScore * 0.5) + (iaScore * 0.3) + (ebScore * 0.2));

        // 2. Operación (40%) — desde usage/analytics si disponible
        let opsScore = 90; // baseline razonable
        let handoffsCount = health.handoffs;
        let slaAvg: number | undefined;

        try {
          const { data: usage } = await api.get("/billing/usage");
          if (usage?.pending_handoffs !== undefined) {
            handoffsCount = usage.pending_handoffs;
            // SLA: si >5 handoffs pendientes, penalizar
            const handoffPenalty = Math.min(handoffsCount * 8, 40);
            opsScore = Math.max(100 - handoffPenalty, 30);
          }
        } catch { /* ops usa baseline */ }

        // 3. Negocio (20%) — billing + quotas
        let bizScore = 100;
        try {
          const { data: sub } = await api.get("/billing/subscription");
          if (sub?.status === "overdue" || sub?.status === "cancelled") bizScore = 0;
          else if (sub?.status === "warning") bizScore = 60;
        } catch { /* biz usa baseline */ }

        // ─── Score compuesto final ──────────────────────────────────────────
        const score = Math.round((infraScore * 0.4) + (opsScore * 0.4) + (bizScore * 0.2));
        const status: HealthStatus =
          score >= 90 ? "healthy" :
          score >= 60 ? "warning" :
          "critical";

        // Trackear si cae a crítico
        if (status === "critical" && health.status !== "critical") {
          TRACK.HEALTH_CRITICAL_SEEN(score);
        }

        setHealth({
          status, score, infraScore, opsScore, bizScore,
          channels: {
            connected: Math.max(connectedCh, isConnected ? 1 : 0),
            total: Math.max(channelEntries.length, 1),
          },
          ia: { status: iaStatus, latencyMs: iaLatency },
          handoffs: handoffsCount,
          slaAvgMin: slaAvg,
        });
      } catch {
        setHealth(prev => ({
          ...prev,
          status: isConnected ? "warning" : "critical",
          score: isConnected ? 65 : 30,
          ia: { status: "slow" },
        }));
      }
    };

    compute();
    const interval = setInterval(compute, 120_000); // 2 min — reduce server load
    return () => clearInterval(interval);
  }, [isConnected]);

  // ─── Reactivo a handoffs desde EventBus ──────────────────────────────────
  useEffect(() => {
    const handoffCount = history.filter(e => e.type === "CONVERSATION_HANDOFF").length;
    if (handoffCount !== health.handoffs) {
      setHealth(prev => ({ ...prev, handoffs: handoffCount }));
    }
  }, [history]);

  // ─── Config visual por estado ─────────────────────────────────────────────
  const cfg = {
    healthy: {
      bg: "bg-transparent",
      border: "border-white/[0.04]",
      dot: "bg-emerald-500",
      dotGlow: false,        // ← sin animación en estado saludable (anti-fatiga)
      text: "text-emerald-400/80",
      label: FLUX_LEXICON.HEALTHY,
      icon: CheckCircle2,
    },
    warning: {
      bg: "bg-amber-500/[0.03]",
      border: "border-amber-500/15",
      dot: "bg-amber-500",
      dotGlow: true,
      text: "text-amber-400",
      label: FLUX_LEXICON.WARNING,
      icon: AlertTriangle,
    },
    critical: {
      bg: "bg-red-500/[0.04]",
      border: "border-red-500/20",
      dot: "bg-red-500",
      dotGlow: true,
      text: "text-red-400",
      label: FLUX_LEXICON.CRITICAL,
      icon: AlertTriangle,
    },
    processing: {
      bg: "bg-cyan-500/[0.03]",
      border: "border-cyan-500/10",
      dot: "bg-cyan-400",
      dotGlow: false,
      text: "text-cyan-400/80",
      label: FLUX_LEXICON.PROCESSING,
      icon: Activity,
    },
  }[health.status];

  const StatusIcon = cfg.icon;

  return (
    <div className={cn("w-full border-b transition-all duration-500", cfg.bg, cfg.border)}>
      {/* ─── Barra compacta siempre visible ─────────────────────────────── */}
      <button
        onClick={() => {
          setExpanded(e => !e);
          if (!expanded) TRACK.HEALTH_EXPANDED();
        }}
        className="w-full flex items-center justify-between px-6 py-2 hover:bg-white/[0.015] transition-colors"
      >
        <div className="flex items-center gap-4">
          {/* Indicador de estado */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <div className={cn("h-2 w-2 rounded-full", cfg.dot)} />
              {cfg.dotGlow && (
                <div className={cn("h-2 w-2 rounded-full absolute inset-0 animate-ping opacity-40", cfg.dot)} />
              )}
            </div>
            <span className={cn("text-[11px] font-semibold tracking-wide", cfg.text)}>
              {cfg.label}
            </span>
          </div>

          {/* Métricas rápidas — solo en md+ */}
          <div className="hidden md:flex items-center gap-3 text-[11px] text-slate-500 font-medium">
            <span className="flex items-center gap-1">
              {isConnected
                ? <Wifi className="h-3 w-3 text-emerald-500/50" />
                : <WifiOff className="h-3 w-3 text-red-500/70" />}
              EventBus
            </span>

            <span className="text-white/[0.06]">·</span>

            <span className="flex items-center gap-1">
              <Bot className={cn("h-3 w-3", health.ia.status === "ok" ? "text-emerald-500/50" : "text-amber-500/70")} />
              {health.ia.status === "ok" ? "IA ✓" : health.ia.status === "slow" ? "IA lenta" : "IA ✗"}
              {health.ia.latencyMs && (
                <span className="text-slate-600">{health.ia.latencyMs}ms</span>
              )}
            </span>

            <span className="text-white/[0.06]">·</span>

            <span className="flex items-center gap-1">
              <Activity className="h-3 w-3 text-slate-500" />
              {health.channels.connected}/{health.channels.total} {FLUX_LEXICON.CONNECTORS}
            </span>

            {health.handoffs > 0 && (
              <>
                <span className="text-white/[0.06]">·</span>
                <span className="flex items-center gap-1 text-amber-500/80">
                  <Clock className="h-3 w-3" />
                  {health.handoffs} handoff{health.handoffs > 1 ? "s" : ""}
                </span>
              </>
            )}
          </div>
        </div>

        {/* Score numérico (solo Growth/Enterprise) */}
        <div className="flex items-center gap-3">
          {showNumericScore && (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-slate-600 font-medium">Score</span>
              <span className={cn(
                "text-xs font-bold tabular-nums",
                health.score >= 90 ? "text-emerald-400/70" :
                health.score >= 60 ? "text-amber-400" : "text-red-400"
              )}>
                {health.score}
              </span>
            </div>
          )}
          <ChevronDown className={cn(
            "h-3 w-3 text-slate-600 transition-transform duration-200",
            expanded && "rotate-180"
          )} />
        </div>
      </button>

      {/* ─── Panel expandido con desglose 40/40/20 ───────────────────────── */}
      {expanded && (
        <div className="px-6 pb-3 grid grid-cols-2 md:grid-cols-4 gap-2 animate-in fade-in slide-in-from-top-1 duration-200">
          <ScoreCard label="Infraestructura" value={health.infraScore} weight="40%" icon={Wifi} />
          <ScoreCard label="Operación" value={health.opsScore} weight="40%" icon={Activity} />
          <ScoreCard label="Negocio" value={health.bizScore} weight="20%" icon={MessageSquare} />
          <ScoreCard label="Score Global" value={health.score} weight="Total" icon={StatusIcon} highlight />
        </div>
      )}
    </div>
  );
}

// ─── Score Card ──────────────────────────────────────────────────────────────
function ScoreCard({ label, value, weight, icon: Icon, highlight }: {
  label: string; value: number; weight: string; icon: any; highlight?: boolean;
}) {
  const color = value >= 90 ? "text-emerald-400" : value >= 60 ? "text-amber-400" : "text-red-400";
  const bg = highlight ? "bg-white/[0.03] border-white/10" : "bg-transparent border-white/[0.04]";

  return (
    <div className={cn("rounded-xl border px-4 py-2.5", bg)}>
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center gap-1.5">
          <Icon className="h-3 w-3 text-slate-500" />
          <span className="text-[10px] font-semibold text-slate-500 uppercase tracking-wider">{label}</span>
        </div>
        <span className="text-[9px] text-slate-600">{weight}</span>
      </div>
      <p className={cn("text-xl font-black tabular-nums", color)}>{value}<span className="text-xs font-normal text-slate-600 ml-0.5">/100</span></p>
    </div>
  );
}
