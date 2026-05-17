"use client";

import { useEffect, useState } from "react";
import { Cpu, Download, CheckCircle, AlertCircle, RefreshCw, Box } from "lucide-react";
import { api } from "@/lib/api";
import { toast } from "sonner";

type AIModel = {
  name: string;
  size_gb: number;
  modified: string;
  active: boolean;
};

export default function ModelsPage() {
  const [models, setModels] = useState<AIModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [pulling, setPulling] = useState(false);
  const [newModel, setNewModel] = useState("");

  const fetchModels = async () => {
    try {
      setLoading(true);
      const res = await api.get("/admin/models");
      setModels(res.data);
    } catch (e) {
      toast.error("Error al conectar con el motor Ollama");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModels();
  }, []);

  const handlePull = async () => {
    if (!newModel) return;
    try {
      setPulling(true);
      toast.info(`Iniciando descarga de ${newModel}...`);
      await api.post(`/admin/models/pull?model_name=${newModel}`);
      toast.success("Descarga iniciada. El model aparecerá cuando termine.");
      setNewModel("");
    } catch (e) {
      toast.error("Error al solicitar descarga");
    } finally {
      setPulling(false);
    }
  };

  return (
    <div className="space-y-8 animate-entry">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-100">Modelos IA (Cerebros)</h1>
          <p className="text-slate-500 text-sm mt-1">Control directo sobre el motor Ollama y cerebros disponibles</p>
        </div>
        <button
          onClick={fetchModels}
          className="flex items-center gap-2 border border-slate-700 hover:border-slate-600 text-slate-400 hover:text-slate-200 px-3 py-2 rounded-lg text-sm transition-all"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Actualizar
        </button>
      </div>

      {/* Descargar Nuevo Modelo */}
      <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
        <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4">Pull New Brain</h2>
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Box className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
            <input 
              type="text" 
              placeholder="Ej: llama3, mistral:7b, qwen2.5:latest..."
              className="w-full bg-slate-950 border border-slate-800 rounded-xl py-3 pl-10 pr-4 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
              value={newModel}
              onChange={(e) => setNewModel(e.target.value)}
            />
          </div>
          <button 
            onClick={handlePull}
            disabled={pulling || !newModel}
            className="bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white px-6 py-3 rounded-xl font-medium transition-all flex items-center gap-2"
          >
            {pulling ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
            Descargar
          </button>
        </div>
      </div>

      {/* Lista de Modelos */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {loading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="h-44 bg-slate-900/50 border border-slate-800 animate-pulse rounded-2xl" />
          ))
        ) : models.length === 0 ? (
          <div className="col-span-3 bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center">
            <Cpu size={32} className="text-slate-700 mx-auto mb-3" />
            <p className="text-slate-400 text-sm font-medium">No hay modelos disponibles</p>
            <p className="text-slate-600 text-xs mt-1">Descarga un model usando el formulario de arriba</p>
          </div>
        ) : (
          models.map((m) => (
            <div key={m.name} className={`bg-slate-900 border ${m.active ? 'border-indigo-500/40 ring-1 ring-indigo-500/20' : 'border-slate-800'} p-5 rounded-2xl shadow-xl hover:translate-y-[-2px] transition-all`}>
              <div className="flex justify-between items-start mb-4">
                <div className="p-2.5 bg-slate-950 rounded-xl border border-slate-800">
                  <Cpu className={`w-5 h-5 ${m.active ? 'text-indigo-400' : 'text-slate-500'}`} />
                </div>
                {m.active && (
                  <span className="bg-indigo-500/10 text-indigo-400 text-[10px] font-bold px-2.5 py-1 rounded-full border border-indigo-500/20">
                    ACTIVO
                  </span>
                )}
              </div>
              <h3 className="text-slate-100 font-bold text-base truncate mb-1">{m.name}</h3>
              <div className="flex items-center gap-3 text-xs text-slate-500 mb-4">
                <span>{m.size_gb} GB</span>
                <span className="text-slate-700">•</span>
                <span className="flex items-center gap-1">
                  <CheckCircle className="w-3 h-3 text-emerald-500" /> Listo
                </span>
              </div>
              <div className="pt-4 border-t border-slate-800/50 flex justify-between items-center">
                <span className="text-[10px] text-slate-600">Modificado: {new Date(m.modified).toLocaleDateString()}</span>
                {!m.active && (
                  <button
                    onClick={() => toast.success(`${m.name} establecido como model por defecto`)}
                    className="text-[10px] font-bold text-indigo-400 hover:text-indigo-300 bg-indigo-500/10 hover:bg-indigo-500/20 px-2.5 py-1 rounded-lg transition-all"
                  >
                    Establecer Default
                  </button>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Alerta de Ingeniería */}
      <div className="bg-amber-900/10 border border-amber-500/20 p-4 rounded-xl flex gap-3 items-start">
        <AlertCircle className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
        <div className="text-sm">
            <h4 className="font-bold text-amber-400 mb-1">Nota de Ingeniería</h4>
            <p className="text-amber-500/80 leading-relaxed">
                Los modelos se ejecutan en hardware dedicado con aceleración por GPU. Descargar modelos de más de 7B parámetros puede impactar la latencia de inferencia en tiempo real si el sistema está bajo carga alta.
            </p>
        </div>
      </div>
    </div>
  );
}
