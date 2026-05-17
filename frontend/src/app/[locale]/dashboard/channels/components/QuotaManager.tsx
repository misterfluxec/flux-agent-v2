"use client";

import { useState, useEffect, useCallback } from "react";
import {
  BarChart3, Globe, MessageCircle, Zap, ChevronDown, ChevronUp,
  Key, RefreshCw, CheckCircle2, Loader2, AlertCircle, Info
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";

interface UsageStat {
  used: number;
  limit: number;
  remaining: number;
}

interface QuotaConfig {
  plan: string;
  quota_mode: string;
  preferred_channel: string;
  auto_fallback_enabled: boolean;
  byoa: {
    enabled: boolean;
    cloud_configured: boolean;
    evolution_configured: boolean;
    cloud_token_masked: string | null;
    phone_number_id: string | null;
    waba_id: string | null;
    evolution_url: string | null;
  };
  usage: {
    cloud_api: UsageStat;
    evolution_api: UsageStat;
  };
  next_reset_at: string | null;
  alert: { remaining_pct: number; reset_date: string; message: string } | null;
}

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

function UsageBar({ stat, label, color }: { stat: UsageStat; label: string; color: string }) {
  const isUnlimited = stat.limit === -1;
  const pct = isUnlimited ? 0 : Math.min(100, (stat.used / stat.limit) * 100);
  const isCritical = !isUnlimited && pct >= 90;
  const isWarning = !isUnlimited && pct >= 70;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="font-medium">{label}</span>
        <span className="text-muted-foreground">
          {isUnlimited ? (
            <span className="text-emerald-500 font-semibold">Ilimitado</span>
          ) : (
            `${stat.remaining.toLocaleString()} restantes`
          )}
        </span>
      </div>
      <div className="h-2 bg-secondary rounded-full overflow-hidden">
        {!isUnlimited && (
          <div
            className={`h-full rounded-full transition-all duration-500 ${
              isCritical ? "bg-red-500" : isWarning ? "bg-yellow-500" : color
            }`}
            style={{ width: `${pct}%` }}
          />
        )}
      </div>
      {!isUnlimited && (
        <p className="text-xs text-muted-foreground">
          {stat.used.toLocaleString()} / {stat.limit.toLocaleString()} usados
        </p>
      )}
    </div>
  );
}

const MODE_OPTIONS = [
  {
    value: "global_pool",
    label: "Pool Global",
    icon: "🏢",
    desc: "FluxAgent gestiona tus mensajes. Cuotas incluidas en tu plan.",
  },
  {
    value: "hybrid",
    label: "Híbrido",
    icon: "🔄",
    desc: "Usa el pool global y activa tus credenciales propias si se agota.",
  },
  {
    value: "byoa",
    label: "BYOA",
    icon: "🔑",
    desc: "Bring Your Own API. Tus mensajes se facturan directo a tu cuenta de Meta.",
  },
];

export default function QuotaManager() {
  const [config, setConfig] = useState<QuotaConfig | null>(null);
  const [loading, setLoading] = useState(true);
  const [switchingMode, setSwitchingMode] = useState(false);
  const [showByoaForm, setShowByoaForm] = useState(false);
  const [savingByoa, setSavingByoa] = useState(false);

  const [byoaForm, setByoaForm] = useState({
    cloud_token: "",
    phone_number_id: "",
    waba_id: "",
    evolution_url: "",
    evolution_api_key: "",
    admin_whatsapp_number: "",
  });

  const fetchConfig = useCallback(async () => {
    try {
      const data = await apiFetch("/quota/my-config");
      setConfig(data);
    } catch (e: any) {
      toast.error(`Error cargando cuotas: ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchConfig();
  }, [fetchConfig]);

  const handleSwitchMode = async (newMode: string) => {
    if (config?.quota_mode === newMode) return;
    setSwitchingMode(true);
    try {
      await apiFetch("/quota/switch-mode", {
        method: "POST",
        body: JSON.stringify({ new_mode: newMode }),
      });
      toast.success(`Modo cambiado a ${newMode}`);
      await fetchConfig();
    } catch (e: any) {
      toast.error(e.message);
    } finally {
      setSwitchingMode(false);
    }
  };

  const handleSaveBYOA = async () => {
    setSavingByoa(true);
    try {
      await apiFetch("/quota/byoa", {
        method: "PUT",
        body: JSON.stringify(byoaForm),
      });
      toast.success("✅ Credenciales BYOA guardadas correctamente");
      setShowByoaForm(false);
      await fetchConfig();
    } catch (e: any) {
      toast.error(`Error guardando BYOA: ${e.message}`);
    } finally {
      setSavingByoa(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-card rounded-2xl border border-border p-8 flex items-center justify-center">
        <Loader2 className="w-6 h-6 animate-spin text-indigo-500" />
      </div>
    );
  }

  if (!config) return null;

  const resetDate = config.next_reset_at
    ? new Date(config.next_reset_at).toLocaleDateString("es-ES", {
        day: "2-digit", month: "long", year: "numeric",
      })
    : "—";

  return (
    <div className="bg-card rounded-2xl border border-border overflow-hidden shadow-sm">
      {/* Header */}
      <div className="p-5 border-b border-border flex items-center justify-between">
        <h2 className="font-semibold flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-indigo-500" /> Gestión de Cuotas
        </h2>
        <div className="flex items-center gap-2">
          <span className="text-xs bg-secondary px-2 py-1 rounded-full capitalize text-muted-foreground">
            Plan: <strong>{config.plan || "custom"}</strong>
          </span>
          <button
            onClick={fetchConfig}
            className="p-1.5 rounded-lg hover:bg-secondary transition-colors"
            title="Actualizar"
          >
            <RefreshCw className="w-4 h-4 text-muted-foreground" />
          </button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Barras de consumo */}
        <div className="space-y-5">
          <UsageBar
            stat={config.usage.cloud_api}
            label="☁️ WhatsApp Cloud API (Meta Oficial)"
            color="bg-emerald-500"
          />
          <UsageBar
            stat={config.usage.evolution_api}
            label="⚡ Evolution API"
            color="bg-indigo-500"
          />
        </div>

        {/* Reset date */}
        <p className="text-xs text-muted-foreground flex items-center gap-1">
          <Info className="w-3 h-3" />
          Las cuotas se renuevan automáticamente el{" "}
          <strong className="text-foreground">{resetDate}</strong>
        </p>

        {/* Selector de modo */}
        <div className="space-y-3">
          <label className="text-sm font-medium">Modo de Consumo</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {MODE_OPTIONS.map((mode) => {
              const isActive = config.quota_mode === mode.value;
              return (
                <button
                  key={mode.value}
                  onClick={() => handleSwitchMode(mode.value)}
                  disabled={switchingMode}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${
                    isActive
                      ? "border-indigo-500 bg-indigo-500/10"
                      : "border-border hover:border-indigo-500/40 bg-background"
                  }`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-lg">{mode.icon}</span>
                    <span className={`text-sm font-semibold ${isActive ? "text-indigo-500" : ""}`}>
                      {mode.label}
                    </span>
                    {isActive && <CheckCircle2 className="w-4 h-4 text-indigo-500 ml-auto" />}
                  </div>
                  <p className="text-xs text-muted-foreground leading-snug">{mode.desc}</p>
                </button>
              );
            })}
          </div>
        </div>

        {/* Sección BYOA (visible si no es global_pool) */}
        {config.quota_mode !== "global_pool" && (
          <div className="border border-border rounded-xl overflow-hidden">
            <button
              onClick={() => setShowByoaForm(!showByoaForm)}
              className="w-full p-4 flex items-center justify-between hover:bg-secondary/50 transition-colors"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    config.byoa.cloud_configured || config.byoa.evolution_configured
                      ? "bg-emerald-500/20 text-emerald-500"
                      : "bg-secondary text-muted-foreground"
                  }`}
                >
                  <Key className="w-4 h-4" />
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium">Credenciales BYOA</p>
                  <p className="text-xs text-muted-foreground">
                    {config.byoa.cloud_configured || config.byoa.evolution_configured
                      ? "✅ Configuradas"
                      : "⚠️ Sin configurar"}
                  </p>
                </div>
              </div>
              {showByoaForm ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </button>

            {showByoaForm && (
              <div className="p-5 border-t border-border space-y-5 bg-secondary/20">
                {/* Cloud API section */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold flex items-center gap-2">
                    <Globe className="w-4 h-4 text-emerald-500" /> WhatsApp Cloud API
                    {config.byoa.cloud_configured && (
                      <span className="text-xs bg-emerald-500/10 text-emerald-600 px-2 py-0.5 rounded-full">
                        Configurado: {config.byoa.cloud_token_masked}
                      </span>
                    )}
                  </h4>
                  <input
                    type="password"
                    placeholder="System User Access Token (EAABm0Px...)"
                    value={byoaForm.cloud_token}
                    onChange={(e) => setByoaForm({ ...byoaForm, cloud_token: e.target.value })}
                    className="w-full px-4 py-2.5 bg-background rounded-xl border border-border text-sm outline-none focus:border-indigo-500"
                  />
                  <div className="grid grid-cols-2 gap-3">
                    <input
                      type="text"
                      placeholder="Phone Number ID"
                      value={byoaForm.phone_number_id}
                      onChange={(e) => setByoaForm({ ...byoaForm, phone_number_id: e.target.value })}
                      className="px-4 py-2.5 bg-background rounded-xl border border-border text-sm outline-none focus:border-indigo-500"
                    />
                    <input
                      type="text"
                      placeholder="WABA ID"
                      value={byoaForm.waba_id}
                      onChange={(e) => setByoaForm({ ...byoaForm, waba_id: e.target.value })}
                      className="px-4 py-2.5 bg-background rounded-xl border border-border text-sm outline-none focus:border-indigo-500"
                    />
                  </div>
                </div>

                {/* Evolution section */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold flex items-center gap-2">
                    <MessageCircle className="w-4 h-4 text-green-500" /> Evolution API
                    {config.byoa.evolution_configured && (
                      <span className="text-xs bg-green-500/10 text-green-600 px-2 py-0.5 rounded-full">
                        Configurado: {config.byoa.evolution_url}
                      </span>
                    )}
                  </h4>
                  <input
                    type="url"
                    placeholder="URL de tu servidor Evolution (https://evolution.tudominio.com)"
                    value={byoaForm.evolution_url}
                    onChange={(e) => setByoaForm({ ...byoaForm, evolution_url: e.target.value })}
                    className="w-full px-4 py-2.5 bg-background rounded-xl border border-border text-sm outline-none focus:border-indigo-500"
                  />
                  <input
                    type="password"
                    placeholder="API Key de Evolution"
                    value={byoaForm.evolution_api_key}
                    onChange={(e) => setByoaForm({ ...byoaForm, evolution_api_key: e.target.value })}
                    className="w-full px-4 py-2.5 bg-background rounded-xl border border-border text-sm outline-none focus:border-indigo-500"
                  />
                </div>

                {/* Notificaciones */}
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold flex items-center gap-2">
                    <Zap className="w-4 h-4 text-yellow-500" /> Notificaciones de cuota baja
                  </h4>
                  <input
                    type="tel"
                    placeholder="Tu número de WhatsApp admin (ej: 5930912345678)"
                    value={byoaForm.admin_whatsapp_number}
                    onChange={(e) => setByoaForm({ ...byoaForm, admin_whatsapp_number: e.target.value })}
                    className="w-full px-4 py-2.5 bg-background rounded-xl border border-border text-sm outline-none focus:border-indigo-500"
                  />
                  <p className="text-xs text-muted-foreground flex items-center gap-1">
                    <AlertCircle className="w-3 h-3" />
                    Recibirás un mensaje cuando tu cuota sea menor al 10%
                  </p>
                </div>

                <Button
                  onClick={handleSaveBYOA}
                  disabled={savingByoa}
                  className="w-full rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white"
                >
                  {savingByoa ? (
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                  )}
                  Guardar Credenciales
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
