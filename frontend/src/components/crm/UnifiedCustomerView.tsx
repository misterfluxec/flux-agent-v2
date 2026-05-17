"use client";

import { useState } from "react";
import { 
  Users, LayoutGrid, List, Search, Filter, Plus, 
  ArrowRight, Phone, Mail, TrendingUp, RefreshCw 
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { TooltipProvider } from "@/components/ui/tooltip";

// Tipos unificados
export type CustomerStatus = 'lead' | 'active' | 'churned' | 'vip';

export interface UnifiedCustomer {
  id: string;
  name: string;
  email: string;
  phone: string;
  status: CustomerStatus;
  pipelineStage?: 'nuevo' | 'contactado' | 'interesado' | 'cerrado';
  value: number;
  lastInteraction: string;
  source: string;
}

const STATUS_CONFIG: Record<CustomerStatus, { label: string; color: string }> = {
  lead: { label: 'Prospecto', color: 'text-amber-400 bg-amber-500/10 border-amber-500/20' },
  active: { label: 'Activo', color: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' },
  churned: { label: 'Inactivo', color: 'text-slate-400 bg-slate-500/10 border-slate-500/20' },
  vip: { label: 'VIP', color: 'text-purple-400 bg-purple-500/10 border-purple-500/20' },
};

const PIPELINE_STAGES = ['nuevo', 'contactado', 'interesado', 'cerrado'];

interface Props {
  initialData: UnifiedCustomer[];
}

export function UnifiedCustomerView({ initialData }: Props) {
  const [viewMode, setViewMode] = useState<'pipeline' | 'directory'>('pipeline');
  const [search, setSearch] = useState("");
  const [filterSource, setFilterSource] = useState("all");

  const filtered = initialData.filter(c => {
    const matchesSearch = c.name.toLowerCase().includes(search.toLowerCase()) || 
                          c.email.toLowerCase().includes(search.toLowerCase());
    const matchesSource = filterSource === "all" || c.source === filterSource;
    return matchesSearch && matchesSource;
  });

  return (
    <div className="space-y-6">
      {/* ── Sub-Header Táctico ── */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div>
          <h2 className="text-2xl font-black text-white/90 tracking-tight">
            Clientes <span className="text-emerald-400">360°</span>
          </h2>
          <p className="text-sm text-white/50 mt-1 font-light">
            Vista unificada de leads y directorio de clientes convertidos.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="bg-black/40 backdrop-blur-md p-1 rounded-xl border border-white/5 flex">
            <button 
              onClick={() => setViewMode('pipeline')}
              className={cn(
                "p-2 rounded-lg transition-all flex items-center gap-2",
                viewMode === 'pipeline' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white'
              )}
            >
              <LayoutGrid className="w-4 h-4" />
              <span className="text-xs font-bold hidden sm:block">Pipeline</span>
            </button>
            <button 
              onClick={() => setViewMode('directory')}
              className={cn(
                "p-2 rounded-lg transition-all flex items-center gap-2",
                viewMode === 'directory' ? 'bg-white/10 text-white shadow-lg' : 'text-white/40 hover:text-white'
              )}
            >
              <List className="w-4 h-4" />
              <span className="text-xs font-bold hidden sm:block">Directorio</span>
            </button>
          </div>

          <button className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">
            <Plus className="w-4 h-4" />
            <span className="hidden sm:block">Nuevo</span>
          </button>
        </div>
      </div>

      {/* ── Filtros ── */}
      <div className="flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <input
            placeholder="Buscar por name o correo..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full h-11 pl-11 pr-4 bg-black/20 border border-white/5 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500/50 transition-all"
          />
        </div>
        <select 
          value={filterSource}
          onChange={(e) => setFilterSource(e.target.value)}
          className="h-11 px-4 bg-black/20 border border-white/5 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500/50 appearance-none min-w-[160px]"
        >
          <option value="all">Origen: Todos</option>
          <option value="whatsapp">WhatsApp</option>
          <option value="web">Web</option>
        </select>
      </div>

      {/* ── Contenido Principal ── */}
      {viewMode === 'pipeline' ? (
        <div className="flex gap-4 overflow-x-auto pb-8 snap-x custom-scrollbar">
          {PIPELINE_STAGES.map((stage) => {
            const stageLeads = filtered.filter(c => c.status === 'lead' && c.pipelineStage === stage);
            return (
              <div key={stage} className="flex-none w-80 bg-black/20 rounded-[24px] border border-white/5 p-4 snap-start flex flex-col min-h-[500px]">
                <div className="flex items-center justify-between mb-4 px-2">
                  <h3 className="font-bold text-white/80 capitalize flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
                    {stage}
                  </h3>
                  <span className="text-xs text-white/40 font-mono">{stageLeads.length}</span>
                </div>
                
                <div className="space-y-3">
                  {stageLeads.map(lead => (
                    <div key={lead.id} className="bg-white/5 border border-white/5 rounded-2xl p-4 hover:bg-white/10 transition-all cursor-pointer group">
                      <div className="flex justify-between items-start mb-2">
                        <h4 className="font-bold text-white text-sm truncate">{lead.name}</h4>
                        <span className="text-emerald-400 text-xs font-bold">${lead.value}</span>
                      </div>
                      <div className="text-[11px] text-white/40 space-y-1">
                        <div className="flex items-center gap-2"><Mail className="w-3 h-3" /> {lead.email}</div>
                        <div className="flex items-center gap-2"><Phone className="w-3 h-3" /> {lead.phone}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-black/40 border border-white/5 rounded-[24px] overflow-hidden">
          <table className="w-full text-left">
            <thead className="bg-white/5 border-b border-white/5 text-[10px] uppercase tracking-widest text-white/40">
              <tr>
                <th className="px-6 py-4">Cliente</th>
                <th className="px-6 py-4">Estado</th>
                <th className="px-6 py-4">Origen</th>
                <th className="px-6 py-4">Valor LTV</th>
                <th className="px-6 py-4 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {filtered.map(c => (
                <tr key={c.id} className="hover:bg-white/5 transition-colors group">
                  <td className="px-6 py-4">
                    <p className="text-sm font-bold text-white">{c.name}</p>
                    <p className="text-xs text-white/30">{c.email}</p>
                  </td>
                  <td className="px-6 py-4">
                    <span className={cn("px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border", STATUS_CONFIG[c.status].color)}>
                      {STATUS_CONFIG[c.status].label}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-xs text-white/40 capitalize">{c.source}</span>
                  </td>
                  <td className="px-6 py-4">
                    <span className="text-sm font-black text-emerald-400">${c.value.toLocaleString()}</span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <button className="text-white/20 group-hover:text-white transition-colors">
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
