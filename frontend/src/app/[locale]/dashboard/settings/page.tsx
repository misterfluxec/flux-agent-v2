"use client";

import { useState, useEffect } from "react";
import {
  Building2, Users, CreditCard, Shield, Bell, AlertTriangle,
  Trash2, UserPlus, ExternalLink, Loader2, Check, Crown,
  Key, Activity, Zap, ChevronUp, Download, FileText,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { api, apiRoot, clearBrain } from "@/lib/api";

type TabType = "profile" | "team" | "billing" | "security";

// =============================================================================
// API FUNCTIONS (connected to billing_router + users_router)
// =============================================================================

async function fetchSubscription() {
  const { data } = await api.get("/billing/subscription");
  return data;
}
async function fetchUsage() {
  const { data } = await api.get("/billing/usage");
  return data;
}
async function fetchInvoices() {
  const { data } = await api.get("/billing/invoices");
  return data;
}
async function upgradePlan(plan: string) {
  const { data } = await api.post(`/billing/upgrade?new_plan=${plan}`);
  return data;
}
async function fetchTeamMembers() {
  try {
    const { data } = await api.get("/users");
    return data;
  } catch { return []; }
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function OrganizacionPage() {
  const [activeTab, setActiveTab] = useState<TabType>("profile");

  const tabs = [
    { id: "profile" as const, label: "Empresa", icon: Building2, color: "cyan" },
    { id: "team" as const, label: "Equipo", icon: Users, color: "emerald" },
    { id: "billing" as const, label: "Facturación", icon: CreditCard, color: "amber" },
    { id: "security" as const, label: "Seguridad", icon: Shield, color: "blue" },
  ];

  return (
    <div className="space-y-6 animate-in fade-in duration-700 pb-12 px-4 md:px-8 max-w-6xl mx-auto pt-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-black tracking-tight text-white/90">Organización</h1>
        <p className="text-white/40 text-sm mt-1">Empresa, equipo, facturación y seguridad de tu operación.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Tab Navigation */}
        <div className="lg:col-span-1 space-y-1">
          {tabs.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold transition-all ${
                  active
                    ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/15"
                    : "text-white/30 hover:bg-white/5 hover:text-white/50 border border-transparent"
                }`}>
                <Icon className={`h-4 w-4 ${active ? "text-cyan-400" : "text-white/20"}`} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Content */}
        <div className="lg:col-span-3">
          <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-6 md:p-8 min-h-[500px]">
            {activeTab === "profile" && <TabProfile />}
            {activeTab === "team" && <TabTeam />}
            {activeTab === "billing" && <TabBilling />}
            {activeTab === "security" && <TabSecurity />}
          </div>

          {/* Danger Zone */}
          <div className="mt-6 bg-red-500/5 border border-red-500/10 rounded-2xl overflow-hidden">
            <div className="flex items-center justify-between p-5">
              <div className="flex items-center gap-3">
                <AlertTriangle className="h-4 w-4 text-red-400/50" />
                <div>
                  <p className="text-sm font-bold text-red-400/70">Resetear Inteligencia</p>
                  <p className="text-[11px] text-white/20">Elimina todos los documentos y productos indexados</p>
                </div>
              </div>
              <Button variant="destructive" size="sm" className="rounded-xl text-xs font-bold"
                onClick={async () => {
                  if (confirm("¿Eliminar TODO el conocimiento entrenado? No se puede deshacer.")) {
                    try {
                      const res = await clearBrain();
                      toast.success(res.mensaje, { description: `${res.chunks_eliminados} chunks eliminados` });
                    } catch { toast.error("Error al vaciar"); }
                  }
                }}>
                <Trash2 className="h-3.5 w-3.5 mr-1.5" /> Vaciar Cerebro IA
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// TAB: EMPRESA
// =============================================================================

function TabProfile() {
  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <SectionHeader icon={Building2} title="Perfil de Empresa" subtitle="Identidad corporativa" color="cyan" />
      <form className="space-y-5" onSubmit={e => { e.preventDefault(); toast.success("Perfil guardado"); }}>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <FormField label="Nombre Legal" defaultValue="Mi Empresa S.A." />
          <FormField label="Industria" type="select" options={["Retail / E-commerce", "Servicios B2B", "Bienes Raíces", "Tecnología", "Salud", "Restaurantes"]} />
        </div>
        <FormField label="Sitio Web" defaultValue="https://" icon={ExternalLink} />
        <FormField label="País" defaultValue="Ecuador" />
        <div className="flex justify-end pt-2">
          <Button className="bg-cyan-500 hover:bg-cyan-600 text-black font-bold rounded-xl px-6">
            Guardar Cambios
          </Button>
        </div>
      </form>
    </div>
  );
}

// =============================================================================
// TAB: EQUIPO (Connected to users_router)
// =============================================================================

function TabTeam() {
  const [members, setMembers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const data = await fetchTeamMembers();
        setMembers(Array.isArray(data) ? data : data.users || []);
      } catch { /* silent */ } finally { setLoading(false); }
    })();
  }, []);

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <div className="flex items-center justify-between">
        <SectionHeader icon={Users} title="Gestión de Equipo" subtitle="Colaboradores" color="emerald" />
        <Button variant="outline" className="rounded-xl border-white/10 text-white/50 hover:text-white hover:bg-white/5 text-xs font-bold gap-1.5">
          <UserPlus className="h-3.5 w-3.5" /> Invitar
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2].map(i => <div key={i} className="h-16 bg-white/[0.02] rounded-xl animate-pulse" />)}
        </div>
      ) : members.length === 0 ? (
        <div className="text-center py-12">
          <Users className="h-8 w-8 text-white/10 mx-auto mb-3" />
          <p className="text-sm font-bold text-white/40">Solo tú por ahora</p>
          <p className="text-xs text-white/20 mt-1">Invita miembros para colaborar en la operación.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {members.map((m: any, i: number) => (
            <div key={i} className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-xl hover:border-white/10 transition-colors">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-emerald-500/10 flex items-center justify-center text-xs font-bold text-emerald-400">
                  {(m.name || m.email || "U")[0].toUpperCase()}
                </div>
                <div>
                  <p className="text-sm font-bold text-white/70">{m.name || m.email}</p>
                  <p className="text-[11px] text-white/30">{m.email}</p>
                </div>
              </div>
              <span className="text-[10px] px-2.5 py-1 rounded-lg bg-white/5 text-white/30 font-bold uppercase tracking-wider">
                {m.role || m.role || "member"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// TAB: FACTURACIÓN (Connected to billing_router)
// =============================================================================

const PLANS = [
  { id: "free", name: "Free", price: 0, agents: 1, messages: 100, color: "white/30" },
  { id: "basic", name: "Basic", price: 29, agents: 2, messages: 2000, color: "blue-400" },
  { id: "pro", name: "Pro", price: 99, agents: 5, messages: 10000, color: "cyan-400" },
  { id: "enterprise", name: "Enterprise", price: 299, agents: 20, messages: 100000, color: "amber-400" },
];

function TabBilling() {
  const [sub, setSub] = useState<any>(null);
  const [usage, setUsage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [s, u] = await Promise.all([fetchSubscription(), fetchUsage()]);
        setSub(s);
        setUsage(u);
      } catch { /* silent */ } finally { setLoading(false); }
    })();
  }, []);

  const handleUpgrade = async (planId: string) => {
    setUpgrading(planId);
    try {
      const res = await upgradePlan(planId);
      toast.success(res.message);
      const [s, u] = await Promise.all([fetchSubscription(), fetchUsage()]);
      setSub(s);
      setUsage(u);
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || "Error al cambiar plan");
    } finally { setUpgrading(null); }
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <SectionHeader icon={CreditCard} title="Plan & Facturación" subtitle="Suscripción" color="amber" />

      {loading ? (
        <div className="space-y-4">
          <div className="h-32 bg-white/[0.02] rounded-2xl animate-pulse" />
          <div className="h-20 bg-white/[0.02] rounded-2xl animate-pulse" />
        </div>
      ) : (
        <>
          {/* Current Plan Card */}
          {sub && (
            <div className="bg-gradient-to-br from-cyan-500/10 to-transparent border border-cyan-500/15 rounded-2xl p-6 relative overflow-hidden">
              <div className="absolute top-4 right-4">
                <span className="text-[10px] font-bold px-2.5 py-1 rounded-lg bg-emerald-500/20 text-emerald-400 border border-emerald-500/20">
                  {sub.status || "Activo"}
                </span>
              </div>
              <div className="flex items-center gap-2 mb-1">
                <Crown className="h-4 w-4 text-cyan-400" />
                <span className="text-[10px] font-bold uppercase tracking-wider text-cyan-400/60">Plan Actual</span>
              </div>
              <h3 className="text-2xl font-black text-white">{sub.plan?.toUpperCase() || "FREE"}</h3>
              <div className="flex items-end gap-1 mt-2">
                <span className="text-3xl font-black text-white">${sub.price || 0}</span>
                <span className="text-sm text-white/30 mb-1">/ mes</span>
              </div>
              <div className="flex gap-4 mt-4 text-xs text-white/40">
                <span>{sub.max_agents || 1} agentes</span>
                <span>·</span>
                <span>{(sub.max_messages_month || 100).toLocaleString()} msgs/mes</span>
              </div>
            </div>
          )}

          {/* Usage */}
          {usage && (
            <div className="grid grid-cols-2 gap-3">
              <UsageBar label="Agentes" used={usage.agents?.used || 0} limit={usage.agents?.limit || 1} />
              <UsageBar label="Mensajes" used={usage.messages?.used || 0} limit={usage.messages?.limit || 100} />
            </div>
          )}

          {/* Plan Comparison */}
          <div>
            <p className="text-xs font-bold text-white/20 uppercase tracking-wider mb-3">Planes Disponibles</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {PLANS.map(plan => {
                const isCurrent = sub?.plan === plan.id;
                return (
                  <div key={plan.id} className={`p-4 rounded-xl border transition-all ${
                    isCurrent ? "bg-cyan-500/10 border-cyan-500/20" : "bg-white/[0.02] border-white/5 hover:border-white/10"
                  }`}>
                    <p className="text-xs font-bold text-white/50">{plan.name}</p>
                    <p className="text-lg font-black text-white mt-1">${plan.price}<span className="text-[10px] text-white/20">/m</span></p>
                    <p className="text-[10px] text-white/20 mt-1">{plan.agents} agentes · {plan.messages.toLocaleString()} msgs</p>
                    {isCurrent ? (
                      <div className="mt-3 flex items-center gap-1 text-[10px] font-bold text-cyan-400">
                        <Check className="h-3 w-3" /> Actual
                      </div>
                    ) : (
                      <Button size="sm" variant="ghost" onClick={() => handleUpgrade(plan.id)} disabled={!!upgrading}
                        className="mt-3 h-7 text-[10px] font-bold text-white/30 hover:text-white/60 w-full">
                        {upgrading === plan.id ? <Loader2 className="h-3 w-3 animate-spin" /> : (
                          plan.price > (sub?.price || 0) ? (
                            <><ChevronUp className="h-3 w-3 mr-1" /> Upgrade</>
                          ) : "Cambiar"
                        )}
                      </Button>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// =============================================================================
// TAB: SEGURIDAD
// =============================================================================

function TabSecurity() {
  const [toggles, setToggles] = useState({ whatsapp: true, twofa: false });

  return (
    <div className="space-y-6 animate-in fade-in duration-300">
      <SectionHeader icon={Shield} title="Seguridad & Notificaciones" subtitle="Protección" color="blue" />

      <div className="space-y-3">
        <ToggleRow icon={Bell} title="Notificaciones WhatsApp" desc="Alertas críticas de ventas y handoffs"
          enabled={toggles.whatsapp} onToggle={() => setToggles(t => ({ ...t, whatsapp: !t.whatsapp }))} />
        <ToggleRow icon={Shield} title="Autenticación 2FA" desc="Protección extra para tu equipo"
          enabled={toggles.twofa} onToggle={() => setToggles(t => ({ ...t, twofa: !t.twofa }))} />
      </div>

      <div className="pt-4 border-t border-white/5 space-y-3">
        <p className="text-xs font-bold text-white/20 uppercase tracking-wider">Acceso API</p>
        <div className="flex items-center gap-3 p-4 bg-white/[0.02] border border-white/5 rounded-xl">
          <Key className="h-4 w-4 text-white/20" />
          <div className="flex-1">
            <p className="text-xs font-bold text-white/50">API Key del Tenant</p>
            <p className="text-[10px] text-white/20 font-mono mt-0.5">flux_••••••••••••••••</p>
          </div>
          <Button variant="ghost" size="sm" className="text-[10px] font-bold text-white/30 h-7">Regenerar</Button>
        </div>

        <div className="flex items-center gap-3 p-4 bg-white/[0.02] border border-white/5 rounded-xl">
          <Activity className="h-4 w-4 text-white/20" />
          <div className="flex-1">
            <p className="text-xs font-bold text-white/50">Logs de Auditoría</p>
            <p className="text-[10px] text-white/20 mt-0.5">Registro completo de acciones del sistema</p>
          </div>
          <Button variant="ghost" size="sm" className="text-[10px] font-bold text-white/30 h-7">Ver Logs</Button>
        </div>
      </div>

      {/* Compliance Export */}
      <div className="pt-4 border-t border-white/5 space-y-3">
        <p className="text-xs font-bold text-white/20 uppercase tracking-wider">Exportación & Compliance</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
          <ExportButton label="Conversaciones" desc="CSV con historial de chats" onClick={() => exportCSV("conversations")} />
          <ExportButton label="Facturas" desc="CSV con historial de billing" onClick={() => exportCSV("invoices")} />
          <ExportButton label="Conocimiento" desc="CSV con fuentes indexadas" onClick={() => exportCSV("knowledge")} />
        </div>
        <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4 mt-2">
          <p className="text-[10px] text-white/20">
            <strong className="text-white/30">Política de retención:</strong> Los datos se retienen por 90 días.
            Para solicitar eliminación completa según RGPD/LOPD, contacta a <span className="text-cyan-400/50">soporte@fluxagent.io</span>
          </p>
        </div>
      </div>
    </div>
  );
}

// =============================================================================
// SHARED COMPONENTS
// =============================================================================

function SectionHeader({ icon: Icon, title, subtitle, color }: { icon: any; title: string; subtitle: string; color: string }) {
  return (
    <div className="flex items-center gap-3 pb-5 border-b border-white/5">
      <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
        <Icon className="h-5 w-5 text-cyan-400" />
      </div>
      <div>
        <h2 className="text-lg font-black text-white">{title}</h2>
        <p className="text-[10px] text-white/20 font-bold uppercase tracking-widest">{subtitle}</p>
      </div>
    </div>
  );
}

function FormField({ label, defaultValue, type, options, icon: Icon }: {
  label: string; defaultValue?: string; type?: string; options?: string[]; icon?: any;
}) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs font-bold text-white/40 ml-1">{label}</label>
      {type === "select" ? (
        <select className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-cyan-500/40 appearance-none">
          {options?.map(o => <option key={o} className="bg-[#111]">{o}</option>)}
        </select>
      ) : (
        <div className="relative">
          {Icon && <Icon className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-white/20" />}
          <input type="text" defaultValue={defaultValue}
            className={`w-full bg-white/5 border border-white/10 rounded-xl ${Icon ? "pl-11" : "pl-4"} pr-4 py-3 text-sm text-white placeholder:text-white/20 focus:outline-none focus:border-cyan-500/40`} />
        </div>
      )}
    </div>
  );
}

function UsageBar({ label, used, limit }: { label: string; used: number; limit: number }) {
  const pct = Math.min((used / limit) * 100, 100);
  const color = pct > 90 ? "bg-red-500" : pct > 70 ? "bg-amber-500" : "bg-cyan-500";
  return (
    <div className="bg-white/[0.02] border border-white/5 rounded-xl p-4">
      <div className="flex justify-between text-xs mb-2">
        <span className="font-bold text-white/40">{label}</span>
        <span className="text-white/60 font-bold">{used.toLocaleString()} / {limit.toLocaleString()}</span>
      </div>
      <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color} transition-all duration-500`} style={{ width: `${pct}%` }} />
      </div>
      <p className="text-[10px] text-white/20 mt-1.5">{pct.toFixed(0)}% utilizado</p>
    </div>
  );
}

function ToggleRow({ icon: Icon, title, desc, enabled, onToggle }: {
  icon: any; title: string; desc: string; enabled: boolean; onToggle: () => void;
}) {
  return (
    <div className="flex items-center justify-between p-4 bg-white/[0.02] border border-white/5 rounded-xl">
      <div className="flex items-center gap-3">
        <Icon className="h-4 w-4 text-white/20" />
        <div>
          <p className="text-sm font-bold text-white/60">{title}</p>
          <p className="text-[11px] text-white/25">{desc}</p>
        </div>
      </div>
      <button onClick={onToggle} className={`w-10 h-5 rounded-full p-0.5 transition-colors ${enabled ? "bg-cyan-500" : "bg-white/10"}`}>
        <div className={`h-4 w-4 rounded-full bg-white transition-transform ${enabled ? "translate-x-5" : "translate-x-0"}`} />
      </button>
    </div>
  );
}

function ExportButton({ label, desc, onClick }: { label: string; desc: string; onClick: () => void }) {
  return (
    <button onClick={onClick}
      className="flex items-center gap-3 p-3 bg-white/[0.02] border border-white/5 rounded-xl hover:border-cyan-500/15 hover:bg-cyan-500/[0.03] transition-all text-left group">
      <div className="h-8 w-8 rounded-lg bg-white/5 flex items-center justify-center group-hover:bg-cyan-500/10 transition-colors">
        <Download className="h-3.5 w-3.5 text-white/20 group-hover:text-cyan-400 transition-colors" />
      </div>
      <div>
        <p className="text-xs font-bold text-white/50">{label}</p>
        <p className="text-[10px] text-white/20">{desc}</p>
      </div>
    </button>
  );
}

async function exportCSV(type: "conversations" | "invoices" | "knowledge") {
  const endpoints: Record<string, string> = {
    conversations: "/conversations",
    invoices: "/billing/invoices",
    knowledge: "/knowledge",
  };

  try {
    const { data } = await api.get(endpoints[type]);
    const items = Array.isArray(data) ? data : data.items || data.results || [data];

    if (items.length === 0) {
      toast.error("No hay datos para exportar");
      return;
    }

    // Auto-detect CSV headers from first object
    const headers = Object.keys(items[0]);
    const csvRows = [headers.join(",")];

    for (const item of items) {
      const row = headers.map(h => {
        const val = item[h];
        const str = typeof val === "object" ? JSON.stringify(val) : String(val ?? "");
        return `"${str.replace(/"/g, '""')}"`;
      });
      csvRows.push(row.join(","));
    }

    const blob = new Blob([csvRows.join("\n")], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `fluxagent_${type}_${new Date().toISOString().split("T")[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    toast.success(`${items.length} registros exportados`);
  } catch {
    toast.error("Error al exportar datos");
  }
}
