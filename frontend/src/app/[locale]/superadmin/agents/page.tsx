"use client";

import { useEffect, useState } from "react";
import { Settings, Bot, ShieldCheck, Zap, MoreHorizontal, ExternalLink, Search, Filter, Database, BrainCircuit } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

type Agent = {
  id: string;
  name: string;
  type: string;
  status: string;
  tenant: string;
};

export default function GlobalAgentsPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAgents = async () => {
      try {
        const res = await api.get("/admin/agents");
        setAgents(res.data);
      } catch (e) {
        toast.error("Error al cargar agentes globales");
      } finally {
        setLoading(false);
      }
    };
    fetchAgents();
  }, []);

  return (
    <div className="space-y-8 animate-entry">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Bot className="w-6 h-6 text-blue-400" />
            Inventario Global de Agentes
          </h1>
          <p className="text-slate-400 text-sm mt-1">Supervisión técnica de todas las instancias de IA desplegadas</p>
        </div>
        <div className="flex gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Buscar por name o type..."
              className="bg-slate-900 border border-slate-800 rounded-lg py-2 pl-10 pr-4 text-sm text-slate-200 focus:outline-none focus:ring-1 focus:ring-blue-500/50"
            />
          </div>
          <button className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2">
            <Zap className="w-4 h-4" />
            Despliegue Maestro
          </button>
        </div>
      </div>

      {/* Grid de Agentes */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="h-48 bg-slate-900/50 border border-slate-800 animate-pulse rounded-2xl" />
          ))
        ) : (
          agents.map((a) => (
            <div key={a.id} className="bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-xl hover:border-blue-500/30 transition-all group relative overflow-hidden">
              {/* Background Glow */}
              <div className="absolute -right-4 -top-4 w-20 h-20 bg-blue-500/5 blur-2xl group-hover:bg-blue-500/10 transition-all" />
              
              <div className="flex justify-between items-start mb-4">
                <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800 group-hover:border-blue-500/30 transition-all">
                  {a.type === 'ventas' ? <Zap className="w-5 h-5 text-amber-400" /> : <BrainCircuit className="w-5 h-5 text-blue-400" />}
                </div>
                <div className="flex gap-1.5">
                    <span className="bg-slate-950 text-[10px] text-slate-400 px-2 py-1 rounded-md border border-slate-800">
                        {a.type.toUpperCase()}
                    </span>
                    <button className="p-1 hover:bg-slate-800 rounded-md text-slate-500">
                        <MoreHorizontal className="w-4 h-4" />
                    </button>
                </div>
              </div>

              <h3 className="text-slate-100 font-bold mb-1 truncate">{a.name}</h3>
              <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-4">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" />
                <span className="truncate">{a.tenant}</span>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-800/50">
                <div className="flex items-center gap-1.5">
                  <div className={`w-1.5 h-1.5 rounded-full ${a.status === 'is_active' ? 'bg-emerald-500 shadow-[0_0_8px_#10b981]' : 'bg-slate-600'}`} />
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-tighter">{a.status}</span>
                </div>
                <button className="text-[10px] font-bold text-blue-400 hover:text-blue-300 flex items-center gap-1 uppercase tracking-tighter group/btn">
                    Auditar Logs
                    <ExternalLink className="w-3 h-3 group-hover/btn:translate-x-0.5 group-hover/btn:-translate-y-0.5 transition-transform" />
                </button>
              </div>
            </div>
          ))
        )}

        {/* Card de Acceso Directo */}
        <div className="bg-slate-900/40 border border-slate-800 border-dashed p-5 rounded-2xl flex flex-col items-center justify-center text-center group hover:bg-slate-900/60 transition-all cursor-pointer">
            <div className="w-10 h-10 rounded-full bg-slate-950 flex items-center justify-center border border-slate-800 group-hover:scale-110 transition-transform mb-3">
                <Search className="w-5 h-5 text-slate-500" />
            </div>
            <span className="text-sm font-medium text-slate-400">Ver Agentes Inactivos</span>
            <span className="text-[10px] text-slate-600 mt-1">Se filtran por defecto</span>
        </div>
      </div>

      {/* Panel de Ingeniería de Memoria */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex gap-6 items-center">
            <div className="p-4 bg-emerald-500/10 rounded-2xl border border-emerald-500/20">
                <Database className="w-8 h-8 text-emerald-400" />
            </div>
            <div>
                <h4 className="text-slate-100 font-bold text-lg">Vectores Activos</h4>
                <p className="text-slate-400 text-sm">342,109 chunks en base de datos RAG global</p>
                <div className="mt-2 flex gap-4">
                    <span className="text-[10px] text-emerald-400 font-bold bg-emerald-400/5 px-2 py-0.5 rounded border border-emerald-400/20">SALUD: 100%</span>
                    <span className="text-[10px] text-slate-500">Latencia RAG: 12ms</span>
                </div>
            </div>
        </div>
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl flex gap-6 items-center">
            <div className="p-4 bg-blue-500/10 rounded-2xl border border-blue-500/20">
                <BrainCircuit className="w-8 h-8 text-blue-400" />
            </div>
            <div>
                <h4 className="text-slate-100 font-bold text-lg">Inferencia Total</h4>
                <p className="text-slate-400 text-sm">1.2M tokens procesados en las últimas 24h</p>
                <div className="mt-2 flex gap-4">
                    <span className="text-[10px] text-blue-400 font-bold bg-blue-400/5 px-2 py-0.5 rounded border border-blue-400/20">UPTIME: 99.9%</span>
                    <span className="text-[10px] text-slate-500">Carga GPU: 42%</span>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
