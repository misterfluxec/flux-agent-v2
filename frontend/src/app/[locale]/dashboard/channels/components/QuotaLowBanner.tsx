"use client";

import { useState } from "react";
import { AlertTriangle, X, RefreshCw, ArrowUpRight } from "lucide-react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { toast } from "sonner";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:9000/api/v1";

function getToken() {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("flux_token") || "";
}

async function apiFetch(path: string, options?: RequestInit) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${getToken()}`,
      ...(options?.headers || {}),
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Error de conexión" }));
    throw new Error(err.detail || "Error del servidor");
  }
  return res.json();
}

interface QuotaConfig {
  plan: string;
  quota_mode: "global_pool" | "hybrid" | "byoa";
  usage: {
    cloud_api: { used: number; limit: number; remaining: number };
    evolution_api: { used: number; limit: number; remaining: number };
  };
  next_reset_at: string | null;
  byoa: { enabled: boolean; cloud_configured: boolean; evolution_configured: boolean; [key: string]: any };
  alert: { show_banner: boolean; remaining_pct: number; reset_date: string; message: string } | null;
}

interface QuotaLowBannerProps {
  onUpgradeClick?: () => void;
  className?: string;
}

export default function QuotaLowBanner({ onUpgradeClick, className = "" }: QuotaLowBannerProps) {
  const [isDismissed, setIsDismissed] = useState(() => {
    if (typeof window === "undefined") return false;
    return sessionStorage.getItem("quota_banner_dismissed") === "true";
  });

  const { data: quota, isLoading, refetch } = useQuery<QuotaConfig>({
    queryKey: ["quota-config"],
    queryFn: () => apiFetch("/quota/my-config"),
    refetchInterval: 5 * 60 * 1000, // cada 5 minutos
    enabled: !isDismissed,
  });

  const sendAlertMutation = useMutation({
    mutationFn: () =>
      apiFetch("/quota/send-low-quota-alert", { method: "POST" }),
    onSuccess: () => toast.success("📱 Alerta enviada a tu WhatsApp"),
    onError: (e: Error) => toast.error(e.message),
  });

  // Calcular % restante total
  const cloudUsed  = quota?.usage.cloud_api.used  ?? 0;
  const evoUsed    = quota?.usage.evolution_api.used ?? 0;
  const cloudLimit = quota?.usage.cloud_api.limit  ?? 200;
  const evoLimit   = quota?.usage.evolution_api.limit ?? 300;
  const totalLimit = (cloudLimit === -1 ? 0 : cloudLimit) + (evoLimit === -1 ? 0 : evoLimit);
  const totalUsed  = cloudUsed + evoUsed;
  const remainingPct = totalLimit > 0 ? Math.round(((totalLimit - totalUsed) / totalLimit) * 100) : 100;

  // Solo mostrar si hay alert del backend O si el % es < 10%
  const shouldShow = !isDismissed && !isLoading && (
    quota?.alert?.show_banner || remainingPct < 10
  );

  const handleDismiss = () => {
    setIsDismissed(true);
    sessionStorage.setItem("quota_banner_dismissed", "true");
  };

  if (!shouldShow) return null;

  const isCritical = remainingPct <= 5;

  const borderColor = isCritical
    ? "border-red-500/40 bg-red-500/8"
    : "border-orange-500/40 bg-orange-500/8";

  const textColor = isCritical ? "text-red-400" : "text-orange-400";

  const barColor = isCritical
    ? "bg-red-500"
    : remainingPct <= 10
    ? "bg-orange-500"
    : "bg-yellow-500";

  const resetDate = quota?.next_reset_at
    ? new Date(quota.next_reset_at).toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "long",
      })
    : quota?.alert?.reset_date ?? "próximo mes";

  return (
    <div
      className={`relative border rounded-xl p-4 mb-4 transition-all ${borderColor} ${
        isCritical ? "animate-pulse" : ""
      } ${className}`}
    >
      {/* Botón cerrar */}
      <button
        onClick={handleDismiss}
        className="absolute top-3 right-3 p-1 rounded-lg hover:bg-white/10 transition-colors"
        aria-label="Cerrar"
      >
        <X className="w-4 h-4 text-muted-foreground" />
      </button>

      <div className="flex items-start gap-3 pr-7">
        <AlertTriangle className={`w-5 h-5 mt-0.5 shrink-0 ${textColor}`} />

        <div className="flex-1 space-y-2">
          <h4 className={`font-semibold text-sm ${textColor}`}>
            ⚠️ Cuota baja: {remainingPct}% restante
          </h4>

          <p className="text-sm text-muted-foreground">
            {quota?.quota_mode !== "byoa" ? (
              <>
                Usados:{" "}
                <strong className="text-foreground">{totalUsed.toLocaleString()}</strong> /{" "}
                {totalLimit.toLocaleString()} conversaciones.
              </>
            ) : (
              "Modo BYOA is_active — revisa el consumo en tu cuenta de Meta."
            )}
            <br />
            🔄 Se renueva el:{" "}
            <strong className="text-foreground">{resetDate}</strong>
          </p>

          {/* Detalle por canal */}
          {quota?.quota_mode !== "byoa" && (
            <div className="grid grid-cols-2 gap-2 text-xs mt-1">
              <div className="bg-white/5 rounded-lg px-3 py-1.5">
                <span className="text-muted-foreground">Cloud API: </span>
                <span className={
                  (quota?.usage.cloud_api.remaining ?? 0) <= 5
                    ? "text-red-400 font-semibold"
                    : "text-foreground"
                }>
                  {cloudLimit === -1 ? "∞" : quota?.usage.cloud_api.remaining ?? 0}
                </span>
              </div>
              <div className="bg-white/5 rounded-lg px-3 py-1.5">
                <span className="text-muted-foreground">Evolution: </span>
                <span className={
                  (quota?.usage.evolution_api.remaining ?? 0) <= 5
                    ? "text-red-400 font-semibold"
                    : "text-foreground"
                }>
                  {evoLimit === -1 ? "∞" : quota?.usage.evolution_api.remaining ?? 0}
                </span>
              </div>
            </div>
          )}

          {/* Acciones */}
          <div className="flex flex-wrap gap-2 mt-3">
            <button
              onClick={() => (onUpgradeClick ? onUpgradeClick() : undefined)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium rounded-lg transition-colors"
            >
              <ArrowUpRight className="w-3.5 h-3.5" />
              Ampliar cuota
            </button>

            {quota?.byoa.enabled && (
              <button
                onClick={() => sendAlertMutation.mutate()}
                disabled={sendAlertMutation.isPending}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-[#25D366]/90 hover:bg-[#128C7E] text-white text-xs font-medium rounded-lg transition-colors disabled:opacity-50"
              >
                {sendAlertMutation.isPending ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span>📱</span>
                )}
                {sendAlertMutation.isPending ? "Enviando..." : "Enviar recordatorio"}
              </button>
            )}

            <button
              onClick={() => refetch()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-secondary hover:bg-secondary/80 text-muted-foreground text-xs font-medium rounded-lg transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Actualizar
            </button>
          </div>
        </div>
      </div>

      {/* Barra de progreso */}
      <div className="mt-4 h-1.5 bg-white/10 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColor}`}
          style={{ width: `${Math.max(1, remainingPct)}%` }}
        />
      </div>
    </div>
  );
}
