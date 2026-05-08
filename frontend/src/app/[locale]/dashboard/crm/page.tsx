"use client";

import { useEffect, useState, useCallback } from "react";
import { 
  Users, Plus, Search, MessageSquare, Edit, RefreshCw, Filter, 
  Mail, Phone, Calendar, Trash2, LayoutGrid, List, ArrowRight, TrendingUp
} from "lucide-react";
import { fetchLeads, type LeadData } from "@/lib/api";

const statusColors: Record<string, string> = {
  nuevo: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  contactado: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  interesado: "text-purple-400 bg-purple-500/10 border-purple-500/20",
  cerrado: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  perdido: "text-rose-400 bg-rose-500/10 border-rose-500/20",
};

const pipelineStages = ["nuevo", "contactado", "interesado", "cerrado"];

export default function CRMPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [filterOrigen, setFilterOrigen] = useState("all");
  const [leadsData, setLeadsData] = useState<LeadData[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"pipeline" | "list">("pipeline");

  const loadLeads = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchLeads();
      setLeadsData(data);
    } catch (err) {
      console.error("Error fetching leads:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  const stats = {
    total: leadsData.length,
    cerrados: leadsData.filter(l => l.estado === "cerrado").length,
    ingresos: leadsData.filter(l => l.estado === "cerrado").reduce((acc, curr) => acc + curr.monto, 0),
  };

  const filteredLeads = leadsData.filter(lead => {
    const matchesSearch = lead.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          lead.phone.includes(searchTerm) ||
                          lead.email.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilterOrigen = filterOrigen === "all" || lead.canal === filterOrigen;
    return matchesSearch && matchesFilterOrigen;
  });

  return (
    <div className="space-y-6 max-w-[1600px] mx-auto animate-in fade-in duration-700 pb-20">
      
      {/* Background glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-4xl h-96 bg-emerald-500/10 rounded-full blur-[120px] pointer-events-none -z-10" />

      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Users className="w-4 h-4 text-emerald-400" />
            <span className="text-[10px] font-bold uppercase tracking-widest text-emerald-400/80">Gestión de Clientes</span>
          </div>
          <h1 className="text-3xl md:text-4xl font-black text-white/90 tracking-tight">
            Pipeline de <span className="text-emerald-400">Ventas</span>
          </h1>
          <p className="text-sm text-white/50 mt-2 font-light">
            Seguimiento automático de leads generados y cerrados por la IA.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="bg-black/40 backdrop-blur-md p-1 rounded-xl border border-white/5 flex">
            <button 
              onClick={() => setViewMode("pipeline")}
              className={`p-2 rounded-lg transition-colors flex items-center gap-2 ${viewMode === 'pipeline' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'}`}
            >
              <LayoutGrid className="w-4 h-4" />
              <span className="text-xs font-bold hidden sm:block">Kanban</span>
            </button>
            <button 
              onClick={() => setViewMode("list")}
              className={`p-2 rounded-lg transition-colors flex items-center gap-2 ${viewMode === 'list' ? 'bg-white/10 text-white' : 'text-white/40 hover:text-white'}`}
            >
              <List className="w-4 h-4" />
              <span className="text-xs font-bold hidden sm:block">Lista</span>
            </button>
          </div>

          <button
            onClick={loadLeads}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 text-sm font-bold text-white/70 bg-black/40 backdrop-blur-md border border-white/5 rounded-xl hover:bg-white/5 hover:text-white transition-colors disabled:opacity-50"
          >
            <RefreshCw size={16} className={loading ? "animate-spin text-emerald-400" : ""} />
            <span className="hidden sm:block">Sincronizar</span>
          </button>
          
          <button className="flex items-center gap-2 px-4 py-2.5 bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold rounded-xl transition-all shadow-[0_0_15px_rgba(16,185,129,0.3)]">
            <Plus className="w-4 h-4" />
            <span className="hidden sm:block">Nuevo Lead</span>
          </button>
        </div>
      </div>

      {/* Mini Analytics Board */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-[24px] p-6 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-blue-500/10 flex items-center justify-center">
            <Users className="w-6 h-6 text-blue-400" />
          </div>
          <div>
            <p className="text-xs text-white/50 uppercase tracking-wider font-bold mb-1">Total Leads</p>
            <p className="text-2xl font-black text-white/90">{stats.total}</p>
          </div>
        </div>
        <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-[24px] p-6 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/10 flex items-center justify-center">
            <TrendingUp className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <p className="text-xs text-white/50 uppercase tracking-wider font-bold mb-1">Ventas Cerradas</p>
            <p className="text-2xl font-black text-white/90">{stats.cerrados}</p>
          </div>
        </div>
        <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-[24px] p-6 shadow-xl flex items-center gap-4">
          <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 border border-emerald-500/20 flex items-center justify-center">
            <span className="text-xl font-black text-emerald-400">$</span>
          </div>
          <div>
            <p className="text-xs text-white/50 uppercase tracking-wider font-bold mb-1">Ingresos Generados</p>
            <p className="text-2xl font-black text-emerald-400">${stats.ingresos.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-2xl p-3 shadow-xl flex flex-col md:flex-row gap-3">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <input
            placeholder="Buscar por nombre, correo o teléfono..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full h-11 pl-11 pr-4 bg-white/5 border border-white/5 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500/50 placeholder:text-white/30 transition-colors"
          />
        </div>
        <div className="relative min-w-[200px]">
          <Filter className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
          <select 
            value={filterOrigen}
            onChange={(e) => setFilterOrigen(e.target.value)}
            className="w-full h-11 pl-11 pr-8 bg-white/5 border border-white/5 rounded-xl text-sm text-white focus:outline-none focus:border-emerald-500/50 appearance-none transition-colors"
          >
            <option value="all" className="bg-gray-900">Origen: Todos</option>
            <option value="whatsapp" className="bg-gray-900">WhatsApp</option>
            <option value="web" className="bg-gray-900">Sitio Web</option>
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {viewMode === "pipeline" ? (
        /* PIPELINE KANBAN VIEW */
        <div className="flex gap-4 overflow-x-auto pb-8 snap-x">
          {pipelineStages.map((stage) => {
            const stageLeads = filteredLeads.filter(l => l.estado === stage);
            return (
              <div key={stage} className="flex-none w-80 bg-black/20 rounded-[24px] border border-white/5 p-4 snap-start flex flex-col h-[calc(100vh-380px)] min-h-[500px]">
                <div className="flex items-center justify-between mb-4 px-2">
                  <h3 className="font-bold text-white/80 capitalize flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${statusColors[stage].split(' ')[1]}`} />
                    {stage}
                  </h3>
                  <span className="bg-white/10 text-white/60 text-xs px-2 py-0.5 rounded-full font-bold">{stageLeads.length}</span>
                </div>
                
                <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
                  {stageLeads.length === 0 ? (
                    <div className="h-24 border-2 border-dashed border-white/5 rounded-xl flex items-center justify-center text-xs text-white/30 font-light">
                      Sin prospectos
                    </div>
                  ) : (
                    stageLeads.map(lead => (
                      <div key={lead.id} className="bg-white/5 border border-white/5 rounded-2xl p-4 hover:bg-white/10 hover:border-white/10 transition-colors cursor-pointer group">
                        <div className="flex justify-between items-start mb-2">
                          <h4 className="font-bold text-white/90 text-sm truncate pr-2">{lead.name}</h4>
                          <span className="text-emerald-400 text-xs font-bold bg-emerald-500/10 px-2 py-0.5 rounded-full shrink-0">
                            ${lead.monto}
                          </span>
                        </div>
                        <div className="space-y-1 mb-4">
                          {lead.phone && (
                            <div className="flex items-center gap-2 text-xs text-white/40">
                              <Phone className="w-3 h-3" />
                              <span className="truncate">{lead.phone}</span>
                            </div>
                          )}
                          {lead.email && (
                            <div className="flex items-center gap-2 text-xs text-white/40">
                              <Mail className="w-3 h-3" />
                              <span className="truncate">{lead.email}</span>
                            </div>
                          )}
                        </div>
                        <div className="flex items-center justify-between pt-3 border-t border-white/5">
                          <span className="text-[10px] text-white/30 bg-black/50 px-2 py-1 rounded-md uppercase tracking-wider">
                            {lead.canal}
                          </span>
                          <button className="text-white/30 hover:text-emerald-400 transition-colors opacity-0 group-hover:opacity-100">
                            <ArrowRight className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        /* LIST VIEW */
        <div className="bg-black/40 backdrop-blur-xl border border-white/5 rounded-[24px] overflow-hidden shadow-xl">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-white/5 bg-white/5">
                  <th className="px-6 py-4 text-xs font-bold text-white/40 uppercase tracking-widest">Cliente</th>
                  <th className="px-6 py-4 text-xs font-bold text-white/40 uppercase tracking-widest">Contacto</th>
                  <th className="px-6 py-4 text-xs font-bold text-white/40 uppercase tracking-widest">Fase</th>
                  <th className="px-6 py-4 text-xs font-bold text-white/40 uppercase tracking-widest">Origen</th>
                  <th className="px-6 py-4 text-xs font-bold text-white/40 uppercase tracking-widest">Valor</th>
                  <th className="px-6 py-4 text-xs font-bold text-white/40 uppercase tracking-widest text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {loading && filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-white/30 text-sm animate-pulse">
                      Cargando pipeline...
                    </td>
                  </tr>
                ) : filteredLeads.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-white/40 text-sm">
                      No hay leads que coincidan con la búsqueda.
                    </td>
                  </tr>
                ) : (
                  filteredLeads.map((lead) => (
                    <tr key={lead.id} className="hover:bg-white/5 transition-colors group">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center text-sm font-bold text-white/70 shrink-0">
                            {lead.name[0].toUpperCase()}
                          </div>
                          <div>
                            <p className="text-sm font-bold text-white/90">{lead.name}</p>
                            <p className="text-xs text-white/40 mt-0.5">{lead.fecha}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-1.5 text-xs text-white/50">
                            <Mail className="w-3 h-3 text-white/30" /> {lead.email || "—"}
                          </div>
                          <div className="flex items-center gap-1.5 text-xs text-white/50">
                            <Phone className="w-3 h-3 text-white/30" /> {lead.phone || "—"}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`px-3 py-1 text-[10px] font-bold uppercase tracking-wider rounded-full border ${statusColors[lead.estado] || statusColors.nuevo}`}>
                          {lead.estado}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-xs font-medium text-white/50 capitalize bg-white/5 px-2 py-1 rounded-md border border-white/5">
                          {lead.canal}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="text-sm font-bold text-emerald-400">
                          ${lead.monto > 0 ? lead.monto.toLocaleString() : "-"}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button className="p-2 text-white/40 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-xl transition-colors" title="Chat">
                            <MessageSquare className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-white/40 hover:text-blue-400 hover:bg-blue-500/10 rounded-xl transition-colors" title="Editar">
                            <Edit className="w-4 h-4" />
                          </button>
                          <button className="p-2 text-white/40 hover:text-rose-400 hover:bg-rose-500/10 rounded-xl transition-colors" title="Eliminar">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Global CSS for scrollbar override inside Kanban columns */}
      <style dangerouslySetInnerHTML={{__html: `
        .custom-scrollbar::-webkit-scrollbar {
          width: 4px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.2);
        }
      `}} />
    </div>
  );
}
