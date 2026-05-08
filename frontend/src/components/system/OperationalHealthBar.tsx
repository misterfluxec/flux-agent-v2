"use client";

import { useEffect, useState } from "react";
import { useEventBus } from "@/providers/EventBusProvider";
import { fetchHealth, HealthResponse } from "@/lib/api";
import {
  Activity,
  Wifi,
  WifiOff,
  Bot,
  MessageSquare,
  AlertTriangle,
  CheckCircle2,
  ChevronDown,
} from "lucide-react";
import { cn } from "@/lib/utils";

// =============================================================================
// OPERATIONAL HEALTH BAR — Barra Global de Salud Operacional
// Siempre visible en la parte superior del dashboard.
// Fuente: EventBus (tiempo real) + /health endpoint (polling 30s)
// =============================================================================

interface HealthStatus {
  overall: "healthy" | "degraded" | "critical";
  channels: { connected: number; total: number };
  ia: { status: "ok" | "slow" | "down"; latencyMs?: number };
  queue: number; // mensajes sin responder
  handoffs: number; // handoffs pendientes
}

export function OperationalHealthBar() {
  const { isConnected, history } = useEventBus();
  const [health, setHealth] = useState<HealthStatus>({
    overall: "healthy",
    channels: { connected: 1, total: 1 },
    ia: { status: "ok", latencyMs: 120 },
    queue: 0,
    handoffs: 0,
  });
  const [expanded, setExpanded] = useState(false);

  // Polling health endpoint cada 30s
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const data = await fetchHealth();
        const services = data.servicios || {};
        
        // Calcular estado de canales
        const channelServices = Object.entries(services).filter(
          ([k]) => k.includes("whatsapp") || k.includes("telegram") || k.includes("evolution")
        );
        const connectedChannels = channelServices.filter(
          ([, v]) => v.estado === "conectado" || v.estado === "saludable"
        ).length;

        // Estado de IA
        const ollamaService = services["ollama"] || services["ai"] || {};
        const iaLatency = ollamaService.latencia_ms;
        const iaStatus = ollamaService.estado === "saludable"
          ? (iaLatency && iaLatency > 2000 ? "slow" : "ok")
          : "down";

        // Calcular overall
        let overall: HealthStatus["overall"] = "healthy";
        if (iaStatus === "down" || !isConnected) overall = "critical";
        else if (iaStatus === "slow" || connectedChannels < Math.max(channelServices.length, 1)) overall = "degraded";

        setHealth(prev => ({
          ...prev,
          channels: {
            connected: Math.max(connectedChannels, isConnected ? 1 : 0),
            total: Math.max(channelServices.length, 1),
          },
          ia: { status: iaStatus, latencyMs: iaLatency },
          overall,
        }));
      } catch {
        // Si /health falla, marcar como degradado
        setHealth(prev => ({
          ...prev,
          overall: isConnected ? "degraded" : "critical",
          ia: { status: "slow" },
        }));
      }
    };

    checkHealth();
    const interval = setInterval(checkHealth, 30_000);
    return () => clearInterval(interval);
  }, [isConnected]);

  // Conteo reactivo de handoffs del EventBus
  useEffect(() => {
    const handoffCount = history.filter(
      e => e.type === "CONVERSATION_HANDOFF"
    ).length;
    setHealth(prev => ({ ...prev, handoffs: handoffCount }));
  }, [history]);

  const statusConfig = {
    healthy: {
      bg: "bg-emerald-500/5",
      border: "border-emerald-500/10",
      dot: "bg-emerald-500",
      text: "text-emerald-400",
      label: "Operación Saludable",
      icon: CheckCircle2,
    },
    degraded: {
      bg: "bg-amber-500/5",
      border: "border-amber-500/10",
      dot: "bg-amber-500",
      text: "text-amber-400",
      label: "Rendimiento Reducido",
      icon: AlertTriangle,
    },
    critical: {
      bg: "bg-red-500/5",
      border: "border-red-500/10",
      dot: "bg-red-500",
      text: "text-red-400",
      label: "Riesgo Operacional",
      icon: AlertTriangle,
    },
  };

  const config = statusConfig[health.overall];
  const StatusIcon = config.icon;

  return (
    <div
      className={cn(
        "w-full border-b transition-all duration-300",
        config.bg,
        config.border,
      )}
    >
      {/* Compact bar — always visible */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center justify-between px-6 py-2 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-4">
          {/* Status indicator */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <div className={cn("h-2 w-2 rounded-full", config.dot)} />
              {health.overall !== "healthy" && (
                <div className={cn("h-2 w-2 rounded-full absolute inset-0 animate-ping opacity-50", config.dot)} />
              )}
            </div>
            <span className={cn("text-xs font-bold", config.text)}>
              {config.label}
            </span>
          </div>

          {/* Quick metrics */}
          <div className="hidden md:flex items-center gap-4 text-[11px] text-white/40 font-medium">
            <span className="flex items-center gap-1.5">
              {isConnected ? (
                <Wifi className="h-3 w-3 text-emerald-400/70" />
              ) : (
                <WifiOff className="h-3 w-3 text-red-400/70" />
              )}
              EventBus {isConnected ? "✓" : "✗"}
            </span>

            <span className="text-white/10">|</span>

            <span className="flex items-center gap-1.5">
              <Bot className={cn("h-3 w-3", health.ia.status === "ok" ? "text-emerald-400/70" : "text-amber-400/70")} />
              IA {health.ia.status === "ok" ? "✓" : health.ia.status === "slow" ? "Lenta" : "✗"}
              {health.ia.latencyMs && (
                <span className="text-white/20">{health.ia.latencyMs}ms</span>
              )}
            </span>

            <span className="text-white/10">|</span>

            <span className="flex items-center gap-1.5">
              <Activity className="h-3 w-3 text-cyan-400/70" />
              Canales {health.channels.connected}/{health.channels.total}
            </span>

            {health.handoffs > 0 && (
              <>
                <span className="text-white/10">|</span>
                <span className="flex items-center gap-1.5 text-amber-400/80">
                  <MessageSquare className="h-3 w-3" />
                  {health.handoffs} handoff{health.handoffs > 1 ? "s" : ""}
                </span>
              </>
            )}
          </div>
        </div>

        <ChevronDown
          className={cn(
            "h-3.5 w-3.5 text-white/20 transition-transform duration-200",
            expanded && "rotate-180"
          )}
        />
      </button>

      {/* Expanded details — on click */}
      {expanded && (
        <div className="px-6 pb-3 grid grid-cols-2 md:grid-cols-4 gap-3 animate-in fade-in slide-in-from-top-1 duration-200">
          <HealthCard
            label="Event Bus"
            value={isConnected ? "Conectado" : "Desconectado"}
            icon={isConnected ? Wifi : WifiOff}
            status={isConnected ? "ok" : "error"}
          />
          <HealthCard
            label="Motor IA"
            value={health.ia.status === "ok" ? "Operativo" : health.ia.status === "slow" ? "Lento" : "Caído"}
            icon={Bot}
            status={health.ia.status === "ok" ? "ok" : health.ia.status === "slow" ? "warn" : "error"}
            detail={health.ia.latencyMs ? `${health.ia.latencyMs}ms latencia` : undefined}
          />
          <HealthCard
            label="Canales"
            value={`${health.channels.connected} de ${health.channels.total}`}
            icon={Activity}
            status={health.channels.connected >= health.channels.total ? "ok" : "warn"}
            detail="conectados"
          />
          <HealthCard
            label="Handoffs"
            value={String(health.handoffs)}
            icon={MessageSquare}
            status={health.handoffs === 0 ? "ok" : health.handoffs > 3 ? "error" : "warn"}
            detail="pendientes"
          />
        </div>
      )}
    </div>
  );
}

// =============================================================================
// HEALTH CARD — Tarjeta individual de estado
// =============================================================================

function HealthCard({
  label,
  value,
  icon: Icon,
  status,
  detail,
}: {
  label: string;
  value: string;
  icon: React.ComponentType<{ className?: string }>;
  status: "ok" | "warn" | "error";
  detail?: string;
}) {
  const colors = {
    ok: "text-emerald-400 bg-emerald-500/5 border-emerald-500/10",
    warn: "text-amber-400 bg-amber-500/5 border-amber-500/10",
    error: "text-red-400 bg-red-500/5 border-red-500/10",
  };

  return (
    <div className={cn("rounded-xl border px-4 py-3", colors[status])}>
      <div className="flex items-center gap-2 mb-1">
        <Icon className="h-3.5 w-3.5 opacity-70" />
        <span className="text-[10px] font-bold uppercase tracking-wider opacity-60">{label}</span>
      </div>
      <p className="text-sm font-bold">{value}</p>
      {detail && <p className="text-[10px] opacity-50 mt-0.5">{detail}</p>}
    </div>
  );
}
