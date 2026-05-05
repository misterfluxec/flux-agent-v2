"use client";

import { useEffect, useState } from "react";
import { Server, Users, CreditCard, Search, Filter, MoreVertical, Ban, CheckCircle2, TrendingUp, Plus, X, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

type Tenant = {
  id: string;
  nombre: string;
  plan: 'starter' | 'pro' | 'enterprise';
  estado: 'activo' | 'suspendido' | 'cancelado';
  usage: { used: number; limit: number; percent: number };
  contrato: { inicio: string; fin: string };
};

const PLAN_COLORS: Record<string, string> = {
  enterprise: 'text-indigo-400 bg-indigo-500/10 border-indigo-500/20',
  pro:        'text-blue-400  bg-blue-500/10  border-blue-500/20',
  starter:    'text-slate-400 bg-slate-500/10 border-slate-500/20',
};

export default function TenantsPage() {
  const [tenants,  setTenants]  = useState<Tenant[]>([]);
  const [loading,  setLoading]  = useState(true);
  const [search,   setSearch]   = useState("");
  const [menuOpen, setMenuOpen] = useState<string | null>(null);

  useEffect(() => {
    api.get("/admin/tenants")
      .then(r => setTenants(r.data))
      .catch(() => toast.error("Error al cargar tenants"))
      .finally(() => setLoading(false));
  }, []);

  const filtered = tenants.filter(t =>
    t.nombre.toLowerCase().includes(search.toLowerCase())
  );

  const handleSuspend = (id: string) => {
    toast.warning("Función: suspender tenant " + id.slice(0,8));
    setMenuOpen(null);
  };

  return (
    <div className="space-y-8 animate-entry">
      {/* ── Cabecera ── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Tenant HQ</h1>
          <p className="text-slate-500 text-sm mt-1">Gestión de ecosistemas empresariales y cuotas de consumo</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500 pointer-events-none" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              type="text"
              placeholder="Buscar empresa..."
              className="bg-slate-900 border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-emerald-500/50 w-56"
            />
          </div>
          <button className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-emerald-600/20">
            <Plus className="w-4 h-4" />
            Nuevo Tenant
          </button>
        </div>
      </div>

      {/* ── KPIs ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { label: "Total Tenants",    val: tenants.length,                                           icon: Users,       color: "text-emerald-400" },
          { label: "Enterprise",       val: tenants.filter(t => t.plan === 'enterprise').length,      icon: CreditCard,  color: "text-indigo-400" },
          { label: "Mensajes Globales",val: "84k",                                                    icon: TrendingUp,  color: "text-blue-400" },
          { label: "Alertas de Cuota", val: tenants.filter(t => t.usage.percent > 80).length,         icon: Ban,         color: "text-red-400" },
        ].map((s, i) => (
          <div key={i} className="bg-slate-900 border border-slate-800 p-5 rounded-2xl">
            <div className="flex justify-between items-start mb-3">
              <s.icon className={`w-5 h-5 ${s.color}`} />
              <span className="text-[10px] font-bold text-slate-600 uppercase tracking-widest">Live</span>
            </div>
            <div className="text-2xl font-bold text-slate-100">{s.val}</div>
            <div className="text-xs text-slate-500 mt-1">{s.label}</div>
          </div>
        ))}
      </div>

      {/* ── Tabla ── */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead className="bg-slate-950/60 text-[10px] uppercase tracking-widest text-slate-500 font-bold">
              <tr>
                <th className="px-6 py-4">Empresa</th>
                <th className="px-6 py-4">Plan</th>
                <th className="px-6 py-4">Uso Mensual</th>
                <th className="px-6 py-4">Contrato</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {loading
                ? Array.from({ length: 4 }).map((_, i) => (
                    <tr key={i} className="animate-pulse">
                      <td colSpan={6} className="px-6 py-6"><div className="h-4 bg-slate-800 rounded w-3/4" /></td>
                    </tr>
                  ))
                : filtered.map(t => (
                    <tr key={t.id} className="hover:bg-slate-800/30 transition-colors">
                      <td className="px-6 py-5">
                        <div className="font-semibold text-slate-200">{t.nombre}</div>
                        <div className="text-[10px] text-slate-600 font-mono mt-0.5">{t.id.slice(0,8)}…</div>
                      </td>
                      <td className="px-6 py-5">
                        <span className={`text-[10px] font-bold px-2.5 py-1 rounded-md border uppercase ${PLAN_COLORS[t.plan]}`}>
                          {t.plan}
                        </span>
                      </td>
                      <td className="px-6 py-5 w-52">
                        <div className="flex justify-between text-xs mb-1.5">
                          <span className="text-slate-300">{t.usage.used.toLocaleString()} / {t.usage.limit.toLocaleString()}</span>
                          <span className={t.usage.percent > 80 ? 'text-red-400 font-bold' : 'text-slate-500'}>{t.usage.percent}%</span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-700 ${t.usage.percent > 90 ? 'bg-red-500' : t.usage.percent > 70 ? 'bg-amber-500' : 'bg-emerald-500'}`}
                            style={{ width: `${t.usage.percent}%` }}
                          />
                        </div>
                      </td>
                      <td className="px-6 py-5 text-xs text-slate-400">
                        {t.contrato.inicio ? new Date(t.contrato.inicio).toLocaleDateString('es-EC') : '—'}
                        <span className="text-slate-700 mx-1">→</span>
                        {t.contrato.fin && t.contrato.fin !== 'Vitalicio' ? new Date(t.contrato.fin).toLocaleDateString('es-EC') : 'Vitalicio'}
                      </td>
                      <td className="px-6 py-5">
                        <div className="flex items-center gap-2">
                          <div className={`w-1.5 h-1.5 rounded-full ${t.estado === 'activo' ? 'bg-emerald-500 shadow-[0_0_6px_#10b981]' : 'bg-red-500'}`} />
                          <span className="text-xs text-slate-300 capitalize">{t.estado}</span>
                        </div>
                      </td>
                      <td className="px-6 py-5 text-right relative">
                        <button
                          onClick={() => setMenuOpen(menuOpen === t.id ? null : t.id)}
                          className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        {menuOpen === t.id && (
                          <div className="absolute right-6 top-12 z-20 bg-slate-800 border border-slate-700 rounded-xl shadow-xl py-1 w-44">
                            <button onClick={() => { toast.info("Editar plan: " + t.nombre); setMenuOpen(null); }}
                              className="w-full text-left px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition-colors">
                              Editar Plan
                            </button>
                            <button onClick={() => handleSuspend(t.id)}
                              className="w-full text-left px-4 py-2.5 text-sm text-red-400 hover:bg-slate-700 transition-colors">
                              Suspender
                            </button>
                            <button onClick={() => { toast.info("Ver detalles: " + t.nombre); setMenuOpen(null); }}
                              className="w-full text-left px-4 py-2.5 text-sm text-slate-300 hover:bg-slate-700 transition-colors">
                              Ver Detalles
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
            </tbody>
          </table>
        </div>
        <div className="px-6 py-4 bg-slate-950/30 border-t border-slate-800 flex justify-between items-center">
          <span className="text-xs text-slate-500">Mostrando {filtered.length} de {tenants.length} tenants</span>
          <div className="flex gap-2">
            <button className="px-3 py-1 text-xs bg-slate-800 text-slate-400 rounded-lg hover:bg-slate-700 disabled:opacity-40" disabled>← Anterior</button>
            <button className="px-3 py-1 text-xs bg-slate-800 text-slate-400 rounded-lg hover:bg-slate-700 disabled:opacity-40" disabled>Siguiente →</button>
          </div>
        </div>
      </div>
    </div>
  );
}
