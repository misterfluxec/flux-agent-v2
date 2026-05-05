"use client";

import { useEffect, useState } from "react";
import { 
  CreditCard, Receipt, DollarSign, TrendingUp, Users,
  Plus, Search, Download, MoreVertical, CheckCircle,
  XCircle, Clock, AlertTriangle, Edit3, Trash2
} from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.labodegaec.com";

interface Plan {
  id: string;
  nombre: string;
  precio: number;
  periodo: string;
  features: string[];
  usuarios_limit: number;
  popular?: boolean;
}

interface Subscription {
  tenant_id: string;
  tenant_nombre: string;
  plan: string;
  estado: string;
  fecha_renovacion: string;
  monto: number;
}

const PLANES: Plan[] = [
  { id: "starter",    nombre: "Starter",    precio: 0,   periodo: "mes", features: ["1 agente", "500 mensajes/mes", "1 instancia WhatsApp", "Soporte por email"], usuarios_limit: 3 },
  { id: "pro",        nombre: "Pro",        precio: 49,  periodo: "mes", features: ["5 agentes", "5,000 mensajes/mes", "3 instancias WhatsApp", "Reportes avanzados", "Soporte prioritario"], usuarios_limit: 10, popular: true },
  { id: "enterprise", nombre: "Enterprise", precio: 199, periodo: "mes", features: ["20 agentes", "50,000 mensajes/mes", "Instancias ilimitadas", "Marca blanca", "SSO + API Access", "SLA garantizado"], usuarios_limit: 999 },
];

const SUSCRIPCIONES: Subscription[] = [
  { tenant_id: "1", tenant_nombre: "LaBodegaEC",      plan: "pro",        estado: "activa",     fecha_renovacion: "2026-02-15", monto: 49 },
  { tenant_id: "2", tenant_nombre: "TechShop Latam",  plan: "starter",    estado: "trial",      fecha_renovacion: "2026-05-20", monto: 0 },
  { tenant_id: "3", tenant_nombre: "ConstruMax S.A.",  plan: "enterprise", estado: "activa",     fecha_renovacion: "2026-05-01", monto: 199 },
  { tenant_id: "4", tenant_nombre: "MediCare Plus",   plan: "pro",        estado: "suspendida", fecha_renovacion: "2026-04-15", monto: 49 },
];

type TabType = "planes" | "suscripciones" | "pagos";

function StatusBadge({ estado }: { estado: string }) {
  const cfg: Record<string, { cls: string; icon: React.ElementType; label: string }> = {
    activa:     { cls: "bg-emerald-500/10 text-emerald-400", icon: CheckCircle, label: "Activa" },
    trial:      { cls: "bg-amber-500/10  text-amber-400",   icon: Clock,       label: "Trial" },
    suspendida: { cls: "bg-red-500/10    text-red-400",     icon: XCircle,     label: "Suspendida" },
    vencida:    { cls: "bg-red-500/10    text-red-400",     icon: AlertTriangle, label: "Vencida" },
  };
  const c   = cfg[estado] || cfg.suspendida;
  const Icon = c.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium ${c.cls}`}>
      <Icon size={11} /> {c.label}
    </span>
  );
}

export default function BillingPage() {
  const [activeTab, setActiveTab] = useState<TabType>("planes");
  const [search,    setSearch]    = useState("");

  const mrr          = SUSCRIPCIONES.filter(s => s.estado === "activa").reduce((a, s) => a + s.monto, 0);
  const trialCount   = SUSCRIPCIONES.filter(s => s.estado === "trial").length;
  const activeCount  = SUSCRIPCIONES.filter(s => s.estado === "activa").length;
  const filtered     = SUSCRIPCIONES.filter(s => s.tenant_nombre.toLowerCase().includes(search.toLowerCase()));

  const TABS: { id: TabType; label: string; icon: React.ElementType }[] = [
    { id: "planes",        label: "Planes",        icon: CreditCard },
    { id: "suscripciones", label: "Suscripciones", icon: Users },
    { id: "pagos",         label: "Historial",     icon: Receipt },
  ];

  return (
    <div className="space-y-8 animate-entry pb-20">
      {/* Cabecera */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Planes &amp; Facturación</h1>
          <p className="text-slate-500 text-sm mt-1">Gestión de planes, suscripciones y pagos de la plataforma</p>
        </div>
        <button
          onClick={() => toast.info("Próximamente: exportar reporte de facturación")}
          className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 px-4 py-2 rounded-lg text-sm font-medium transition-all"
        >
          <Download className="w-4 h-4" /> Exportar
        </button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "MRR",                  val: `$${mrr}`,     icon: DollarSign,  color: "text-emerald-400" },
          { label: "Suscripciones Activas",val: activeCount,    icon: Users,       color: "text-blue-400" },
          { label: "En Trial",             val: trialCount,     icon: Clock,       color: "text-amber-400" },
          { label: "Crecimiento MoM",      val: "+12%",         icon: TrendingUp,  color: "text-indigo-400" },
        ].map((kpi, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
            <kpi.icon className={`w-5 h-5 ${kpi.color} mb-3`} />
            <div className="text-2xl font-bold text-slate-100">{kpi.val}</div>
            <div className="text-xs text-slate-500 mt-1">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 p-1 bg-slate-900 border border-slate-800 rounded-xl w-fit">
        {TABS.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-5 py-2 rounded-lg text-sm font-semibold transition-all ${
              activeTab === tab.id
                ? "bg-slate-700 text-slate-100 shadow"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            <tab.icon size={14} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* ── Tab: Planes ── */}
      {activeTab === "planes" && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANES.map(plan => (
            <div key={plan.id} className={`relative bg-slate-900 border rounded-2xl p-6 flex flex-col gap-4 transition-all hover:translate-y-[-2px] ${plan.popular ? 'border-blue-500/40 ring-1 ring-blue-500/20' : 'border-slate-800'}`}>
              {plan.popular && (
                <span className="absolute -top-3 left-6 bg-blue-600 text-white text-[10px] font-bold px-3 py-0.5 rounded-full uppercase tracking-wider">
                  Más Popular
                </span>
              )}
              <div>
                <h3 className="text-lg font-bold text-slate-100">{plan.nombre}</h3>
                <p className="text-xs text-slate-500 mt-0.5">Hasta {plan.usuarios_limit === 999 ? 'usuarios ilimitados' : `${plan.usuarios_limit} usuarios`}</p>
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-4xl font-black text-slate-100">${plan.precio}</span>
                <span className="text-slate-500 text-sm">/{plan.periodo}</span>
              </div>
              <ul className="space-y-2.5 flex-1">
                {plan.features.map((f, i) => (
                  <li key={i} className="flex items-center gap-2.5 text-sm text-slate-300">
                    <CheckCircle size={14} className="text-emerald-400 shrink-0" />
                    {f}
                  </li>
                ))}
              </ul>
              <button
                onClick={() => toast.info(`Editar plan: ${plan.nombre}`)}
                className="w-full flex items-center justify-center gap-2 border border-slate-700 hover:border-slate-600 text-slate-300 hover:text-slate-100 py-2.5 rounded-xl text-sm font-medium transition-all"
              >
                <Edit3 size={14} /> Editar Plan
              </button>
            </div>
          ))}
        </div>
      )}

      {/* ── Tab: Suscripciones ── */}
      {activeTab === "suscripciones" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
          <div className="p-4 border-b border-slate-800 flex gap-3">
            <div className="relative flex-1 max-w-xs">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none" />
              <input
                value={search} onChange={e => setSearch(e.target.value)}
                placeholder="Buscar tenant..."
                className="w-full bg-slate-950 border border-slate-800 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
              />
            </div>
          </div>
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-[10px] uppercase tracking-widest text-slate-500 font-bold">
              <tr>
                <th className="px-6 py-4">Tenant</th>
                <th className="px-6 py-4">Plan</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4">Renovación</th>
                <th className="px-6 py-4 text-right">Monto</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {filtered.map(sub => (
                <tr key={sub.tenant_id} className="hover:bg-slate-800/30 transition-colors">
                  <td className="px-6 py-4 font-semibold text-slate-200 text-sm">{sub.tenant_nombre}</td>
                  <td className="px-6 py-4">
                    <span className="text-[10px] font-bold px-2.5 py-1 rounded-md border uppercase text-blue-400 bg-blue-500/10 border-blue-500/20 capitalize">
                      {sub.plan}
                    </span>
                  </td>
                  <td className="px-6 py-4"><StatusBadge estado={sub.estado} /></td>
                  <td className="px-6 py-4 text-sm text-slate-400">{new Date(sub.fecha_renovacion).toLocaleDateString("es-EC")}</td>
                  <td className="px-6 py-4 text-right font-bold text-slate-100">${sub.monto}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => toast.info("Gestionar suscripción: " + sub.tenant_nombre)}
                      className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="px-6 py-3 border-t border-slate-800 bg-slate-950/30">
            <span className="text-xs text-slate-500">Mostrando {filtered.length} suscripciones</span>
          </div>
        </div>
      )}

      {/* ── Tab: Historial de Pagos ── */}
      {activeTab === "pagos" && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 flex flex-col items-center justify-center gap-4 text-center">
          <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center">
            <Receipt size={28} className="text-slate-500" />
          </div>
          <h3 className="text-base font-semibold text-slate-300">Historial de Pagos</h3>
          <p className="text-sm text-slate-500 max-w-xs leading-relaxed">
            Conecta con Stripe para visualizar el historial de cobros, reembolsos y transacciones fallidas.
          </p>
          <button
            onClick={() => toast.info("Conectar Stripe — próximamente")}
            className="mt-2 bg-indigo-600 hover:bg-indigo-500 text-white px-6 py-2.5 rounded-xl text-sm font-semibold transition-all"
          >
            Conectar Stripe
          </button>
        </div>
      )}
    </div>
  );
}