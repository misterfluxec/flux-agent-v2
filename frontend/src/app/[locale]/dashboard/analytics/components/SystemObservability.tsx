"use client";

import { useState, useEffect } from "react";
import {
  Shield, Activity, RefreshCw, AlertTriangle, CheckCircle2,
  Loader2, Zap, Database, MessageSquare, Bot,
  CircleSlash, CircleDot, Circle, RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { toast } from "sonner";

// =============================================================================
// API
// =============================================================================

async function fetchResilienceHealth() {
  const { data } = await api.get("/resilience/health");
  return data?.data || data;
}

async function fetchResilienceMetrics() {
  const { data } = await api.get("/resilience/metrics");
  return data?.data || data;
}

async function fetchBillingUsage() {
  const { data } = await api.get("/billing/usage");
  return data;
}

async function resetCircuitBreakers() {
  const { data } = await api.post("/resilience/reset/circuit_breaker");
  return data;
}

// =============================================================================
// COMPONENT
// =============================================================================

export function SystemObservability() {
  const [health, setHealth] = useState<any>(null);
  const [metrics, setMetrics] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [resetting, setResetting] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const [h, m, u] = await Promise.allSettled([
        fetchResilienceHealth(),
        fetchResilienceMetrics(),
        fetchBillingUsage(),
      ]);
      if (h.status === "fulfilled") setHealth(h.value);
      if (m.status === "fulfilled") setMetrics(m.value);
      if (u.status === "fulfilled") setUsage(u.value);
    } catch { /* silent */ }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const handleReset = async () => {
    setResetting(true);
    try {
      await resetCircuitBreakers();
      toast.success("Circuit breakers reseteados");
      load();
    } catch {
      toast.error("Error al resetear — verifica permisos admin");
    } finally { setResetting(false); }
  };

  const healthScore = health?.health_score ?? 0;
  const healthStatus = health?.health_status ?? "unknown";
  const scoreColor = healthScore >= 90 ? "text-emerald-400" :
    healthScore >= 60 ? "text-amber-400" : "text-red-400";
  const scoreBg = healthScore >= 90 ? "bg-emerald-500/10 border-emerald-500/20" :
    healthScore >= 60 ? "bg-amber-500/10 border-amber-500/20" : "bg-red-500/10 border-red-500/20";

  const cbData = metrics?.circuit_breakers || {};
  const bhData = metrics?.bulkheads || {};
  const toData = metrics?.timeouts || {};

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 duration-500">

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[1, 2, 3].map(i => <div key={i} className="h-36 bg-white/[0.02] rounded-2xl animate-pulse" />)}
        </div>
      ) : (
        <>
          {/* Health Score + Quick Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Score Card */}
            <div className={`rounded-2xl border p-6 ${scoreBg} relative overflow-hidden`}>
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">Health Score</span>
                <button onClick={load} className="text-white/20 hover:text-white/50 transition-colors">
                  <RefreshCw className="h-3.5 w-3.5" />
                </button>
              </div>
              <div className="flex items-end gap-2">
                <span className={`text-5xl font-black ${scoreColor}`}>{healthScore}</span>
                <span className="text-sm text-white/30 mb-2">/100</span>
              </div>
              <p className={`text-xs font-bold mt-2 ${scoreColor} capitalize`}>{healthStatus}</p>

              {/* Issues */}
              {health?.issues?.total > 0 && (
                <div className="mt-4 pt-3 border-t border-white/5 space-y-1">
                  {health.issues.open_circuits > 0 && (
                    <p className="text-[11px] text-red-400 flex items-center gap-1.5">
                      <CircleSlash className="h-3 w-3" /> {health.issues.open_circuits} circuit(s) abierto(s)
                    </p>
                  )}
                  {health.issues.high_rejection_bulkheads > 0 && (
                    <p className="text-[11px] text-amber-400 flex items-center gap-1.5">
                      <AlertTriangle className="h-3 w-3" /> {health.issues.high_rejection_bulkheads} bulkhead(s) alto rechazo
                    </p>
                  )}
                  {health.issues.high_timeout_rate > 0 && (
                    <p className="text-[11px] text-amber-400 flex items-center gap-1.5">
                      <Activity className="h-3 w-3" /> {health.issues.high_timeout_rate} timeout(s) alto
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* Circuit Breakers */}
            <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">Circuit Breakers</span>
                <Zap className="h-4 w-4 text-white/10" />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <Metric label="Cerrados" value={cbData.closed ?? 0} color="text-emerald-400" />
                <Metric label="Abiertos" value={cbData.open ?? 0} color={cbData.open > 0 ? "text-red-400" : "text-white/40"} />
                <Metric label="Half-Open" value={cbData.half_open ?? 0} color={cbData.half_open > 0 ? "text-amber-400" : "text-white/40"} />
              </div>
              <div className="mt-4 pt-3 border-t border-white/5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] text-white/20">Tasa de fallo promedio</span>
                  <span className={`text-xs font-bold ${(cbData.avg_failure_rate || 0) > 5 ? "text-red-400" : "text-emerald-400"}`}>
                    {(cbData.avg_failure_rate || 0).toFixed(1)}%
                  </span>
                </div>
              </div>
              {cbData.open > 0 && (
                <Button size="sm" onClick={handleReset} disabled={resetting}
                  className="mt-3 w-full bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-xl text-[10px] font-bold h-8 gap-1.5">
                  {resetting ? <Loader2 className="h-3 w-3 animate-spin" /> : <RotateCcw className="h-3 w-3" />}
                  Resetear CBs
                </Button>
              )}
            </div>

            {/* Usage */}
            <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
              <div className="flex items-center justify-between mb-4">
                <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">Uso del Plan</span>
                <span className="text-[10px] font-bold text-cyan-400/60 uppercase">{usage?.plan || "free"}</span>
              </div>
              {usage ? (
                <div className="space-y-4">
                  <UsageBar label="Agentes" used={usage.agents?.used || 0} limit={usage.agents?.limit || 1} icon={Bot} />
                  <UsageBar label="Mensajes" used={usage.messages?.used || 0} limit={usage.messages?.limit || 100} icon={MessageSquare} />
                  <div className="pt-2 border-t border-white/5">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-white/20">Conversaciones activas</span>
                      <span className="text-xs font-bold text-white/50">{usage.conversations || 0}</span>
                    </div>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-white/20">Sin datos de uso disponibles</p>
              )}
            </div>
          </div>

          {/* Resilience Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Bulkheads */}
            <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Database className="h-4 w-4 text-white/20" />
                <span className="text-xs font-bold text-white/40">Bulkheads</span>
                <span className="text-[10px] font-bold text-white/15 ml-auto">{bhData.total || 0} activos</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Peticiones" value={bhData.total_requests ?? 0} color="text-white/50" format />
                <Metric label="Exitosas" value={bhData.successful_requests ?? 0} color="text-emerald-400" format />
                <Metric label="Rechazadas" value={bhData.rejected_requests ?? 0} color={bhData.rejected_requests > 0 ? "text-red-400" : "text-white/40"} format />
                <Metric label="Éxito %" value={Number(bhData.avg_success_rate?.toFixed(1) || 0)} color="text-cyan-400" suffix="%" />
              </div>
            </div>

            {/* Timeouts */}
            <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
              <div className="flex items-center gap-2 mb-4">
                <Activity className="h-4 w-4 text-white/20" />
                <span className="text-xs font-bold text-white/40">Timeouts</span>
                <span className="text-[10px] font-bold text-white/15 ml-auto">{toData.total || 0} configurados</span>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <Metric label="Llamadas" value={toData.total_calls ?? 0} color="text-white/50" format />
                <Metric label="Timeouts" value={toData.timeout_calls ?? 0} color={toData.timeout_calls > 0 ? "text-amber-400" : "text-white/40"} format />
                <Metric label="Éxito %" value={Number(toData.avg_success_rate?.toFixed(1) || 0)} color="text-emerald-400" suffix="%" />
                <Metric label="Timeout %" value={Number(toData.avg_timeout_rate?.toFixed(1) || 0)} color={(toData.avg_timeout_rate || 0) > 5 ? "text-red-400" : "text-white/40"} suffix="%" />
              </div>
            </div>
          </div>

          {/* Services Grid */}
          <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6">
            <h3 className="text-xs font-bold text-white/30 uppercase tracking-widest mb-4">Servicios Protegidos</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {[
                { name: "Ollama (LLM)", icon: Bot },
                { name: "WhatsApp Cloud", icon: MessageSquare },
                { name: "Redis (Cache)", icon: Database },
                { name: "PostgreSQL", icon: Database },
              ].map(svc => (
                <div key={svc.name} className="bg-white/[0.02] border border-white/5 rounded-xl p-4 flex items-center gap-3">
                  <div className="h-8 w-8 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                    <svc.icon className="h-4 w-4 text-emerald-400/60" />
                  </div>
                  <div>
                    <p className="text-xs font-bold text-white/50">{svc.name}</p>
                    <div className="flex items-center gap-1 mt-0.5">
                      <Circle className="h-2 w-2 text-emerald-400 fill-emerald-400" />
                      <span className="text-[10px] text-emerald-400/60">Protegido</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function Metric({ label, value, color, suffix, format }: {
  label: string; value: number; color: string; suffix?: string; format?: boolean;
}) {
  const display = format ? value.toLocaleString() : value;
  return (
    <div>
      <p className="text-[10px] text-white/20 mb-0.5">{label}</p>
      <p className={`text-lg font-black ${color}`}>{display}{suffix || ""}</p>
    </div>
  );
}

function UsageBar({ label, used, limit, icon: Icon }: {
  label: string; used: number; limit: number; icon: any;
}) {
  const pct = Math.min((used / limit) * 100, 100);
  const color = pct > 90 ? "bg-red-500" : pct > 70 ? "bg-amber-500" : "bg-cyan-500";
  return (
    <div>
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-white/30 flex items-center gap-1"><Icon className="h-3 w-3" /> {label}</span>
        <span className="text-[10px] font-bold text-white/40">{used}/{limit}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}
